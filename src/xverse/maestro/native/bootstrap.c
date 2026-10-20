/* BS10: admitted helper roles only; never thaws workload C1 or adopts PIDs. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <linux/memfd.h>
#include <linux/sched.h>
#include <openssl/evp.h>
#include <openssl/hmac.h>
#include <poll.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/random.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/statfs.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
#define NS UINT64_C(1000000000)
#define SEALS (F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL)
#define PACKET 128
#define MAX_IMAGE (32U*1024U*1024U)
#ifdef RUN_BOOTSTRAP
#define CONFIG_MAGIC "BC17"
#define WIRE_MAGIC "BS17"
#define VERSION 2
#define IMAGES 4
#define MAX_ROLE 5
#else
#define CONFIG_MAGIC "BC10"
#define WIRE_MAGIC "BS10"
#define VERSION 1
#define IMAGES 3
#define MAX_ROLE 3
#endif
struct image { int fd; char *argv0; };
struct child { int cg, unit, pidfd; pid_t pid; unsigned role, active; uint64_t deadline; unsigned char token[32]; };
struct supervisor {
    int channel,parent; struct ucred peer; uint64_t generation,lease,sequence,deadline;
    unsigned char scope[32]; unsigned char *config; struct image images[IMAGES]; struct child children[64];
#ifdef RUN_BOOTSTRAP
    int boundary_parent, watched[128]; unsigned watch_count, authority_slot, storage_slot, terminal;
    unsigned char watch_key[32], watch_reply[32]; /* F-02 (finding 403): never sent to the Python peer */
#endif
};
static uint64_t now_ns(void) { struct timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t)||t.tv_sec<0)return 0;return (uint64_t)t.tv_sec*NS+(uint64_t)t.tv_nsec; }
static uint64_t get64(const unsigned char *p) { uint64_t x=0;for(unsigned i=0;i<8;++i)x=(x<<8)|p[i];return x; }
static uint32_t get32(const unsigned char *p) { uint32_t x=0;for(unsigned i=0;i<4;++i)x=(x<<8)|p[i];return x; }
static void put64(unsigned char *p,uint64_t n) { for(unsigned i=0;i<8;++i){p[7-i]=(unsigned char)n;n>>=8;} }
static int decimal(const char *s) { uint64_t n=0;if(!*s||strlen(s)>10)return -1;for(;*s;++s){if(*s<'0'||*s>'9')return -1;n=n*10+(unsigned)(*s-'0');if(n>INT_MAX)return -1;}return n>=3?(int)n:-1; }
static int alive(int fd) { struct pollfd p={.fd=fd,.events=POLLIN};return poll(&p,1,0)==0; }
static int sealed(int fd,off_t maximum,off_t *size) {
    int seals=fcntl(fd,F_GET_SEALS);struct stat s;
    if(seals<0||(seals&SEALS)!=SEALS||fstat(fd,&s)||!S_ISREG(s.st_mode)||s.st_size<=0||s.st_size>maximum)return -1;
    *size=s.st_size;return 0;
}
static int digest_fd(int fd,size_t size,const unsigned char *expected) {
    EVP_MD_CTX *ctx=EVP_MD_CTX_new();int okay=ctx&&EVP_DigestInit_ex(ctx,EVP_sha256(),NULL)==1;
    unsigned char buffer[16384],digest[EVP_MAX_MD_SIZE];unsigned length=0;size_t used=0;
    while(okay&&used<size){size_t amount=size-used;if(amount>sizeof(buffer))amount=sizeof(buffer);
        ssize_t n=pread(fd,buffer,amount,(off_t)used);if(n<=0){okay=0;break;}
        okay=EVP_DigestUpdate(ctx,buffer,(size_t)n)==1;used+=(size_t)n;
    }
    okay=okay&&EVP_DigestFinal_ex(ctx,digest,&length)==1&&length==32&&!memcmp(digest,expected,32);
    EVP_MD_CTX_free(ctx);return okay?0:-1;
}
static int field(int fd,const char *name,const char *key,uint64_t *out) {
    char data[4096];int input=openat(fd,name,O_RDONLY|O_CLOEXEC|O_NOFOLLOW);if(input<0)return -1;
    ssize_t n=read(input,data,sizeof(data)-1);close(input);if(n<=0||(size_t)n==sizeof(data)-1)return -1;data[n]=0;
    char *line=data;unsigned found=0;
    while(*line){char *end=strchr(line,'\n'),*space=strchr(line,' ');if(!end||!space||space>end)return -1;*end=0;*space=0;
        if(!strcmp(line,key)){if(found++||!space[1])return -1;uint64_t value=0;
            for(char *p=space+1;*p;++p){if(*p<'0'||*p>'9'||value>(UINT64_MAX-9)/10)return -1;value=value*10+(unsigned)(*p-'0');}*out=value;}
        line=end+1;
    }return found==1?0:-1;
}
static int cgroup(int fd,int empty) {
    struct stat s;struct statfs fs;uint64_t frozen,populated,descendants;
    return fstat(fd,&s)||!S_ISDIR(s.st_mode)||fstatfs(fd,&fs)||fs.f_type!=0x63677270||
        field(fd,"cgroup.events","frozen",&frozen)||frozen!=1||field(fd,"cgroup.stat","nr_descendants",&descendants)||descendants||
        (empty&&(field(fd,"cgroup.events","populated",&populated)||populated))?-1:0;
}
static int same(int a,int b) { struct stat x,y;return !fstat(a,&x)&&!fstat(b,&y)&&x.st_dev==y.st_dev&&x.st_ino==y.st_ino; }
static int write_freeze(int fd,char value) {
    int control=openat(fd,"cgroup.freeze",O_WRONLY|O_CLOEXEC|O_NOFOLLOW);if(control<0)return (errno==ENOENT||errno==ENODEV)?1:-1;
    ssize_t n=write(control,&value,1);close(control);return n==1?0:-1;
}
static int enabled(struct supervisor *s) {
    struct pollfd p={.fd=s->channel,.events=POLLRDHUP};uint64_t now=now_ns();
    return now&&now<s->deadline&&now<s->lease&&now<s->generation-2*NS&&alive(s->parent)&&
        poll(&p,1,0)>=0&&!(p.revents&(POLLRDHUP|POLLHUP|POLLERR|POLLNVAL));
}
static int respond(struct supervisor *s,unsigned kind,uint64_t slot,struct child *c,int fd) {
    unsigned char p[PACKET]={0};memcpy(p,WIRE_MAGIC,4);p[7]=(unsigned char)kind;put64(p+8,s->sequence);put64(p+16,s->deadline);memcpy(p+24,s->scope,32);put64(p+56,slot);
    if(c){put64(p+64,(uint64_t)c->pid);memcpy(p+72,c->token,32);put64(p+104,c->active);}
    else if(kind!=20)put64(p+104,s->lease);
#ifdef RUN_BOOTSTRAP
    if(!c&&kind==20)memcpy(p+72,s->watch_reply,32);
#endif
    union{struct cmsghdr align;unsigned char data[CMSG_SPACE(sizeof(int))];} control;
    struct iovec iov={.iov_base=p,.iov_len=sizeof(p)};struct msghdr msg={.msg_iov=&iov,.msg_iovlen=1};
    if(fd>=0){memset(&control,0,sizeof(control));msg.msg_control=control.data;msg.msg_controllen=sizeof(control.data);
        struct cmsghdr *h=CMSG_FIRSTHDR(&msg);h->cmsg_level=SOL_SOCKET;h->cmsg_type=SCM_RIGHTS;h->cmsg_len=CMSG_LEN(sizeof(int));memcpy(CMSG_DATA(h),&fd,sizeof(fd));}
    return sendmsg(s->channel,&msg,MSG_DONTWAIT|MSG_NOSIGNAL)==PACKET?0:-1;
}
static int receive(struct supervisor *s,unsigned char *p,int *fds,unsigned *count) {
    union{struct cmsghdr align;unsigned char data[CMSG_SPACE(sizeof(struct ucred))+CMSG_SPACE(8*sizeof(int))];} control;
    struct iovec iov={.iov_base=p,.iov_len=PACKET};struct msghdr msg={.msg_iov=&iov,.msg_iovlen=1,.msg_control=control.data,.msg_controllen=sizeof(control.data)};
    ssize_t n=recvmsg(s->channel,&msg,MSG_DONTWAIT|MSG_CMSG_CLOEXEC);if(n<0)return (errno==EAGAIN||errno==EWOULDBLOCK||errno==EINTR)?1:-1;
    unsigned credentials=0;int valid=n==PACKET&&!(msg.msg_flags&(MSG_TRUNC|MSG_CTRUNC));*count=0;
    for(struct cmsghdr *h=CMSG_FIRSTHDR(&msg);h;h=CMSG_NXTHDR(&msg,h)){
        if(h->cmsg_level==SOL_SOCKET&&h->cmsg_type==SCM_RIGHTS){size_t bytes=h->cmsg_len>=CMSG_LEN(0)?h->cmsg_len-CMSG_LEN(0):0;
            for(size_t i=0;i+sizeof(int)<=bytes;i+=sizeof(int)){int fd;memcpy(&fd,(unsigned char*)CMSG_DATA(h)+i,sizeof(fd));if(*count<8)fds[(*count)++]=fd;else{close(fd);valid=0;}}}
        else if(h->cmsg_level==SOL_SOCKET&&h->cmsg_type==SCM_CREDENTIALS&&h->cmsg_len==CMSG_LEN(sizeof(struct ucred))){struct ucred peer;memcpy(&peer,CMSG_DATA(h),sizeof(peer));
            if(peer.pid!=s->peer.pid||peer.uid!=s->peer.uid||peer.gid!=s->peer.gid)valid=0;
            ++credentials;}
        else valid=0;
    }return valid&&credentials==1?0:-1;
}
static int initialize(struct supervisor *s,int argc,char **argv) {
    if(argc!=3)return -1;
    int channel=decimal(argv[1]),input=decimal(argv[2]);if(channel<0||input<0||channel==input)return -1;
    s->channel=fcntl(channel,F_DUPFD_CLOEXEC,3);off_t size;
    if(s->channel<0||sealed(input,65536,&size)||size<56)return -1;
    s->config=malloc((size_t)size);if(!s->config||pread(input,s->config,(size_t)size,0)!=size||memcmp(s->config,CONFIG_MAGIC,4)||get32(s->config+4)!=VERSION)return -1;
    unsigned length=0;if(EVP_Digest(s->config,(size_t)size,s->scope,&length,EVP_sha256(),NULL)!=1||length!=32)return -1;
#ifdef RUN_BOOTSTRAP
    if(getrandom(s->watch_key,32,0)!=32)return -1;
#endif
    s->generation=get64(s->config+8);s->lease=get64(s->config+16);s->deadline=s->lease;uint64_t now=now_ns();
    if(!now||s->generation<=now+2*NS||s->generation-now>394*NS||s->lease<=now||s->lease-now>5*NS||s->lease>s->generation-2*NS)return -1;
    size_t offset=56;
#ifdef RUN_BOOTSTRAP
    if(size<80)return -1;
    uint64_t parent=get64(s->config+56);struct stat identity;struct statfs filesystem;
    if(parent<3||parent>INT_MAX)return -1;
    s->boundary_parent=fcntl((int)parent,F_DUPFD_CLOEXEC,3);
    if(s->boundary_parent<0||fstat(s->boundary_parent,&identity)||!S_ISDIR(identity.st_mode)||
       fstatfs(s->boundary_parent,&filesystem)||filesystem.f_type!=0x63677270||
       (uint64_t)identity.st_dev!=get64(s->config+64)||(uint64_t)identity.st_ino!=get64(s->config+72))return -1;
    offset=80;
#endif
    for(unsigned i=0;i<IMAGES;++i){if((size_t)size-offset<40)return -1;uint32_t original=get32(s->config+offset),n=get32(s->config+offset+36);
        if(original<3||original>INT_MAX||n==0||n>4096||n>=(size_t)size-offset-40)return -1;
        s->images[i].fd=fcntl((int)original,F_DUPFD_CLOEXEC,3);off_t image_size;
        if(s->images[i].fd<0||sealed(s->images[i].fd,MAX_IMAGE,&image_size)||digest_fd(s->images[i].fd,(size_t)image_size,s->config+offset+4))return -1;
        unsigned char elf[4];if(pread(s->images[i].fd,elf,4,0)!=4||memcmp(elf,"\177ELF",4))return -1;
        offset+=40;s->images[i].argv0=(char*)s->config+offset;
        if(s->config[offset]!='/'||s->config[offset+n]||memchr(s->config+offset,0,n))return -1;
        offset+=(size_t)n+1;
    }
    if(offset!=(size_t)size)return -1;
    int type,pass=1;socklen_t n=sizeof(type),peer_n=sizeof(s->peer);
    if(getsockopt(s->channel,SOL_SOCKET,SO_TYPE,&type,&n)||type!=SOCK_SEQPACKET||getsockopt(s->channel,SOL_SOCKET,SO_PEERCRED,&s->peer,&peer_n)||peer_n!=sizeof(s->peer)||
        s->peer.pid!=getppid()||s->peer.pid<=1||s->peer.uid!=getuid()||s->peer.gid!=getgid()||setsockopt(s->channel,SOL_SOCKET,SO_PASSCRED,&pass,sizeof(pass)))return -1;
    s->parent=(int)syscall(SYS_pidfd_open,s->peer.pid,0);
    return s->parent>=0&&alive(s->parent)&&getppid()==s->peer.pid&&!prctl(PR_SET_DUMPABLE,0,0,0,0)&&!prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)?0:-1;
}
#ifdef RUN_BOOTSTRAP
static int terminal_fence(struct supervisor *s) {
    /* Original retained descriptors only. Never thaw, reopen, or infer waits. */
    if(s->terminal||!s->authority_slot||!s->storage_slot)return -1;
    s->terminal=1; /* Irreversible even if a later freeze observation fails. */
    for(unsigned i=0;i<s->watch_count;++i){
        int result=write_freeze(s->watched[i],'1');
        if(result<0)return -1;
        if(result==1)continue; /* Original removed cgroup cannot accept a new task. */
        uint64_t frozen=0;
        while(enabled(s)){
            if(!field(s->watched[i],"cgroup.events","frozen",&frozen)&&frozen==1)break;
            struct pollfd p={.fd=s->parent,.events=POLLIN};poll(&p,1,1);
        }
        if(frozen!=1||!enabled(s))return -1;
    }
    return enabled(s)?0:-1;
}
/* F-02 (finding 403): WATCH proof the authority verifies natively on ADVANCE. */
static int watch_token(const unsigned char *key,int fd,unsigned char *out) {
    struct stat st;if(fstat(fd,&st))return -1;
    unsigned char message[20];memcpy(message,"MLWT",4);put64(message+4,(uint64_t)st.st_dev);put64(message+12,(uint64_t)st.st_ino);
    unsigned length=0;return HMAC(EVP_sha256(),key,32,message,sizeof(message),out,&length)&&length==32?0:-1;
}
static int watch_boundary(struct supervisor *s,int fd,uint64_t slot) {
    if(slot!=(uint64_t)s->watch_count+1||s->watch_count>=128||!enabled(s)||cgroup(fd,1))return -1;
    int parent=openat(fd,"..",O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if(parent<0)return -1;
    int matched=same(parent,s->boundary_parent);close(parent);if(!matched)return -1;
    for(unsigned i=0;i<s->watch_count;++i)if(same(fd,s->watched[i]))return -1;
    for(unsigned i=0;i<64;++i)if(s->children[i].pid>0&&same(fd,s->children[i].cg))return -1;
    int retained=fcntl(fd,F_DUPFD_CLOEXEC,3);if(retained<0)return -1;
    if(watch_token(s->watch_key,retained,s->watch_reply)){close(retained);return -1;}
    s->watched[s->watch_count++]=retained;return 0;
}
static int authority_input(struct supervisor *s,int fd,off_t size) {
    unsigned char config[2688];
    if(s->authority_slot||!s->watch_count||size<288||size>2688||pread(fd,config,(size_t)size,0)!=size||
       memcmp(config,"AC17",4)||get32(config+4)!=2||get64(config+8)!=s->generation||
       get64(config+16)>s->lease||get64(config+16)<=now_ns())return -1;
    uint64_t units=get64(config+32);if(units<1||units>16||(uint64_t)size!=128+160*units)return -1;
    for(uint64_t u=0;u<units;++u){const unsigned char *record=config+128+160*u;unsigned found=0;
        for(unsigned w=0;w<s->watch_count;++w){struct stat st;
            if(fstat(s->watched[w],&st))return -1;
            if((uint64_t)st.st_dev==get64(record+96)&&(uint64_t)st.st_ino==get64(record+104)){
                if(cgroup(s->watched[w],1))return -1;
                found++;
            }
        }if(found!=1)return -1;
    }return 0;
}
#endif
static int birth(struct supervisor *s,struct child *c,unsigned role,int *fds) {
#ifdef RUN_BOOTSTRAP
    if(role!=3&&role!=4&&role!=5)return -1;
    if(role==3&&s->storage_slot)return -1;
    if(role==5){
        for(unsigned i=0;i<s->watch_count;++i)if(same(fds[0],s->watched[i]))return -1;
        for(unsigned i=0;i<64;++i)if(s->children[i].pid>0&&same(fds[0],s->children[i].cg))return -1;
    }
#endif
    if(c->pid||role<1||role>MAX_ROLE||!enabled(s)||cgroup(fds[0],1)||cgroup(fds[1],0)||((role>=3)!=same(fds[0],fds[1])))return -1;
    int type;socklen_t n=sizeof(type);off_t input_size;
    if(getsockopt(fds[2],SOL_SOCKET,SO_TYPE,&type,&n)||type!=SOCK_SEQPACKET||sealed(fds[3],65536,&input_size))return -1;
#ifdef RUN_BOOTSTRAP
    if(role==4){
        if(authority_input(s,fds[3],input_size))return -1;
        for(unsigned i=0;i<s->watch_count;++i)if(same(fds[0],s->watched[i]))return -1;
    }
#endif
    c->cg=fcntl(fds[0],F_DUPFD_CLOEXEC,3);c->unit=fcntl(fds[1],F_DUPFD_CLOEXEC,3);if(c->cg<0||c->unit<0)return -1;
    c->role=role;c->deadline=s->deadline;
    char cg[32],channel[32],input[32],generation[32],lease[32],heartbeat[32],epoch[32],scope[65];
    snprintf(cg,sizeof(cg),"%d",fds[1]);snprintf(channel,sizeof(channel),"%d",fds[2]);snprintf(input,sizeof(input),"%d",fds[3]);
    unsigned image=role==5?2:role-1;
    char *args[10]={s->images[image].argv0,NULL};
    if(role==1){args[1]=cg;args[2]=channel;args[3]=input;}
    else if(role==2){unsigned char config[64];if(input_size!=64||pread(fds[3],config,64,0)!=64)return -1;
        uint64_t gen=get64(config),until=get64(config+8),beat=get64(config+16);
        if(gen!=s->generation||until>s->lease||until<=now_ns()||beat==0||beat>5*NS)return -1;
        snprintf(generation,sizeof(generation),"%llu",(unsigned long long)gen);snprintf(lease,sizeof(lease),"%llu",(unsigned long long)until);
        snprintf(heartbeat,sizeof(heartbeat),"%llu",(unsigned long long)beat);snprintf(epoch,sizeof(epoch),"%llu",(unsigned long long)get64(config+24));
        const char *hex="0123456789abcdef";for(unsigned i=0;i<32;++i){scope[2*i]=hex[config[32+i]>>4];scope[2*i+1]=hex[config[32+i]&15];}scope[64]=0;
        args[1]=cg;args[2]=channel;args[3]=generation;args[4]=lease;args[5]=heartbeat;args[6]=scope;args[7]=epoch;
    }else if(role==3){args[1]="-I";args[2]="-m";args[3]="xverse.maestro.persistence_worker";args[4]=channel;args[5]=input;}
    else if(role==5){args[1]="-I";args[2]="-m";args[3]="xverse.maestro.controller_worker";args[4]=channel;args[5]=input;}
    else{args[1]=channel;args[2]=input;}
    int keyfd=-1;
#ifdef RUN_BOOTSTRAP
    char key[32];
    if(role==4){ /* F-02: the watch key reaches only the authority, in a sealed memfd */
        keyfd=(int)syscall(SYS_memfd_create,"maestro-watch-key",MFD_CLOEXEC|MFD_ALLOW_SEALING);
        if(keyfd<0)return -1;
        if(write(keyfd,s->watch_key,32)!=32||fcntl(keyfd,F_ADD_SEALS,SEALS)){close(keyfd);return -1;}
        snprintf(key,sizeof(key),"%d",keyfd);args[3]=key;
    }
#endif
    if(getrandom(c->token,32,0)!=32||!enabled(s)){if(keyfd>=0)close(keyfd);return -1;}
    struct clone_args clone={0};clone.flags=CLONE_PARENT|CLONE_PIDFD|CLONE_INTO_CGROUP;clone.cgroup=(__u64)(unsigned)c->cg;clone.pidfd=(uint64_t)(uintptr_t)&c->pidfd;clone.exit_signal=0;
    long pid=syscall(SYS_clone3,&clone,sizeof(clone));
    if(pid==0){
        if(syscall(SYS_close_range,3U,UINT_MAX,4U))_exit(126);
        if(fcntl(fds[2],F_SETFD,0)<0||(role!=2&&fcntl(fds[3],F_SETFD,0)<0)||(role<3&&fcntl(fds[1],F_SETFD,0)<0))_exit(126);
        if(keyfd>=0&&fcntl(keyfd,F_SETFD,0)<0)_exit(126);
        int null=open("/dev/null",O_RDWR|O_CLOEXEC);if(null<0)_exit(126);for(int fd=0;fd<3;++fd)if(dup2(null,fd)<0)_exit(126);
        char *environment[]={NULL};syscall(SYS_execveat,s->images[image].fd,"",args,environment,AT_EMPTY_PATH);_exit(127);
    }
    if(keyfd>=0)close(keyfd);
    if(pid<0)return -1;
    c->pid=(pid_t)pid;
#ifdef RUN_BOOTSTRAP
    if(role==4)s->authority_slot=(unsigned)(c-s->children)+1;
    if(role==3)s->storage_slot=(unsigned)(c-s->children)+1;
#endif
    return enabled(s)&&alive(c->pidfd)&&!cgroup(c->cg,0)?0:-1;
}
static int activate(struct supervisor *s,struct child *c) {
    if(c->active||!enabled(s)||s->deadline>c->deadline||!alive(c->pidfd)||cgroup(c->cg,0)||cgroup(c->unit,0)||write_freeze(c->cg,'0'))return -1;
    c->active=1;uint64_t frozen;
    while(enabled(s)){if(!field(c->cg,"cgroup.events","frozen",&frozen)&&!frozen)return 0;struct pollfd p={.fd=s->parent,.events=POLLIN};poll(&p,1,1);}return -1;
}
static int cleanup(struct supervisor *s) {
    uint64_t now=now_ns(),end=s->generation;if(now&&end>now+2*NS)end=now+2*NS;
    for(unsigned i=0;i<64;++i)if(s->children[i].pid>0)syscall(SYS_pidfd_send_signal,s->children[i].pidfd,SIGKILL,NULL,0);
    int unresolved=0;
    for(unsigned i=0;i<64;++i){struct child *c=&s->children[i];if(c->pid<=0)continue;
        while(alive(c->pidfd)&&now_ns()<end){struct pollfd p={.fd=c->pidfd,.events=POLLIN};poll(&p,1,1);}
        if(alive(c->pidfd))unresolved=1;
        int written=write_freeze(c->unit,'1');if(written<0){unresolved=1;continue;}if(written==1)continue;
        uint64_t frozen=0;while(now_ns()<end){if(!field(c->unit,"cgroup.events","frozen",&frozen)&&frozen==1)break;struct pollfd p={.fd=c->pidfd,.events=POLLIN};poll(&p,1,1);}
        if(frozen!=1)unresolved=1;
    }
#ifdef RUN_BOOTSTRAP
    for(unsigned i=0;i<s->watch_count;++i){
        int written=write_freeze(s->watched[i],'1');if(written<0){unresolved=1;continue;}if(written==1)continue;
        uint64_t frozen=0;while(now_ns()<end){
            if(!field(s->watched[i],"cgroup.events","frozen",&frozen)&&frozen==1)break;
            struct pollfd p={.fd=s->parent,.events=POLLIN};poll(&p,1,1);
        }if(frozen!=1)unresolved=1;
    }
#endif
    return unresolved?70:0;
}
int main(int argc,char **argv) {
    /* F02R-01 (finding 406): not dumpable before the watch key is generated. */
    if(prctl(PR_SET_DUMPABLE,0,0,0,0))return 64;
    struct supervisor s={.channel=-1,.parent=-1};for(unsigned i=0;i<64;++i)s.children[i].cg=s.children[i].unit=s.children[i].pidfd=-1;
    if(initialize(&s,argc,argv))return 64;
    if(respond(&s,16,0,NULL,-1))return cleanup(&s);
    for(;;){
        uint64_t now=now_ns();if(!now||now>=s.lease||now>=s.generation-2*NS||!alive(s.parent))return cleanup(&s);
#ifdef RUN_BOOTSTRAP
        if(!s.terminal&&s.authority_slot&&!alive(s.children[s.authority_slot-1].pidfd))return cleanup(&s);
        if(s.storage_slot&&!alive(s.children[s.storage_slot-1].pidfd))return cleanup(&s);
#endif
        struct pollfd pollers[2]={{.fd=s.parent,.events=POLLIN},{.fd=s.channel,.events=POLLIN|POLLRDHUP}};
        int result=poll(pollers,2,10);if(result<0){if(errno==EINTR)continue;return cleanup(&s);}if(pollers[0].revents||(pollers[1].revents&(POLLRDHUP|POLLHUP|POLLERR|POLLNVAL)))return cleanup(&s);
        if(!(pollers[1].revents&POLLIN))continue;
        unsigned char p[PACKET];int fds[8];unsigned count=0;int received=receive(&s,p,fds,&count);
        if(received==1)continue;
        if(received<0){for(unsigned i=0;i<count;++i)close(fds[i]);return cleanup(&s);}
        unsigned kind=get32(p+4);uint64_t until=get64(p+16),slot=get64(p+56);unsigned char zero[8]={0};
        int valid=received==0&&!memcmp(p,WIRE_MAGIC,4)&&get64(p+8)==s.sequence+1&&!memcmp(p+24,s.scope,32)&&!get64(p+112)&&!memcmp(p+120,zero,8)&&
            until>now_ns()&&until-now_ns()<=5*NS&&until<=s.lease&&until<=s.generation-2*NS;
        #ifdef RUN_BOOTSTRAP
        if(s.terminal&&kind!=6)valid=0;
#endif
        if(valid){s.sequence++;s.deadline=until;
            if(kind==1&&count==4&&slot>=1&&slot<=64&&!get64(p+64)){
                unsigned char token[32]={0};valid=!memcmp(p+72,token,32)&&get64(p+104)>=1&&get64(p+104)<=MAX_ROLE;
                struct child *c=&s.children[slot-1];if(valid)valid=!birth(&s,c,(unsigned)get64(p+104),fds)&&!respond(&s,17,slot,c,c->pidfd);
            }else if(kind==2&&count==0&&slot>=1&&slot<=64&&!get64(p+104)){
                struct child *c=&s.children[slot-1];valid=c->pid>0&&get64(p+64)==(uint64_t)c->pid&&!memcmp(p+72,c->token,32)&&!activate(&s,c)&&!respond(&s,18,slot,c,-1);
            }else if(kind==3&&count==0&&slot==0&&!get64(p+64)){
                unsigned char token[32]={0};uint64_t lease=get64(p+104);valid=!memcmp(p+72,token,32)&&lease>=s.lease&&lease>now_ns()&&lease-now_ns()<=5*NS&&lease<=s.generation-2*NS;
                if(valid){s.lease=lease;valid=!respond(&s,19,0,NULL,-1);}
#ifdef RUN_BOOTSTRAP
            }else if(kind==5&&count==0&&slot==0&&!get64(p+64)&&!get64(p+104)){
                unsigned char token[32]={0};valid=!memcmp(p+72,token,32)&&!terminal_fence(&s)&&!respond(&s,21,0,NULL,-1);
            }else if(kind==6&&count==0&&slot==0&&!get64(p+64)){
                unsigned char token[32]={0};uint64_t lease=get64(p+104);
                valid=s.terminal&&!memcmp(p+72,token,32)&&lease>=s.lease&&lease>now_ns()&&lease-now_ns()<=5*NS&&lease<=s.generation-2*NS;
                if(valid){s.lease=lease;valid=!respond(&s,22,0,NULL,-1);}
            }else if(kind==4&&count==1&&!get64(p+64)&&!get64(p+104)){
                unsigned char token[32]={0};valid=!memcmp(p+72,token,32)&&!watch_boundary(&s,fds[0],slot)&&!respond(&s,20,slot,NULL,-1);
#endif
            }else valid=0;
        }
        for(unsigned i=0;i<count;++i)close(fds[i]);
        if(!valid)return cleanup(&s);
    }
}
