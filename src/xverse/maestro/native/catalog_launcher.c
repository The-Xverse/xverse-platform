/* LC09 catalog Stage only. Never thaws, transfers C1 or claims tree cleanup. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <linux/memfd.h>
#include <linux/sched.h>
#include <openssl/evp.h>
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
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define NS UINT64_C(1000000000)
#define PACKET 128
#define CONFIG_HEADER 104
#define SEALS (F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL)
#define CGROUP2_MAGIC 0x63677270
#define MAX_IMAGE (8U*1024U*1024U)
enum { STAGE=1, CANCEL=2, QUERY=3, FAULT_KILL=4, FAULT_FREEZE=5, FAULT_THAW=6, READY=16, STAGED=17, CANCELLED=18, ERROR=19, OBSERVED=20, FAULTED=21 };
struct launcher {
    int cg, socket, parent, childfd, errorfd, image, cwd;
    struct stat identity;
    struct ucred peer;
    uint64_t generation, sequence, deadline;
    unsigned char scope[32], digest[32], token[32];
    char *argv[65], *env[33], *directory;
    unsigned char *config;
    pid_t child;
    int attempted, reaped, status, exec_closed, exec_error;
};
static uint64_t now_ns(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC,&t) || t.tv_sec<0) return 0;
    return (uint64_t)t.tv_sec*NS+(uint64_t)t.tv_nsec;
}
static uint64_t get64(const unsigned char *p) { uint64_t n=0; for(unsigned i=0;i<8;++i)n=(n<<8)|p[i]; return n; }
static uint32_t get32(const unsigned char *p) { uint32_t n=0; for(unsigned i=0;i<4;++i)n=(n<<8)|p[i]; return n; }
static void put64(unsigned char *p,uint64_t n) { for(unsigned i=0;i<8;++i){p[7-i]=(unsigned char)n;n>>=8;} }
static int decimal(const char *s,int *out) {
    if (!*s || strlen(s)>10) return -1;
    uint64_t n=0;
    for(;*s;++s){if(*s<'0'||*s>'9')return -1;n=n*10+(unsigned)(*s-'0');if(n>INT_MAX)return -1;}
    *out=(int)n;return *out>=3?0:-1;
}
static int alive(int fd) { struct pollfd p={.fd=fd,.events=POLLIN};return poll(&p,1,0)==0; }
static int same_boundary(struct launcher *g) {
    struct stat s;
    return !fstat(g->cg,&s) && S_ISDIR(s.st_mode) && s.st_nlink &&
        s.st_dev==g->identity.st_dev && s.st_ino==g->identity.st_ino;
}
static int field(struct launcher *g,const char *name,const char *key,uint64_t *value) {
    char data[4096];
    int fd=openat(g->cg,name,O_RDONLY|O_CLOEXEC|O_NOFOLLOW);
    if(fd<0)return -1;
    ssize_t n=read(fd,data,sizeof(data)-1); close(fd);
    if(n<=0 || (size_t)n==sizeof(data)-1)return -1;
    data[n]=0;
    char *line=data;int found=0;
    while(*line){
        char *end=strchr(line,'\n');if(!end)return -1;*end=0;
        char *space=strchr(line,' ');if(!space)return -1;*space=0;
        if(!strcmp(line,key)){
            if(found++ || !space[1])return -1;
            uint64_t x=0;
            for(char *p=space+1;*p;++p){if(*p<'0'||*p>'9'||x>(UINT64_MAX-9)/10)return -1;x=x*10+(unsigned)(*p-'0');}
            *value=x;
        }
        line=end+1;
    }
    return found==1?0:-1;
}
static int enabled(struct launcher *g) {
    uint64_t now=now_ns();
    struct pollfd p={.fd=g->socket,.events=POLLRDHUP};
    return now && now<g->deadline && now<g->generation-2*NS && alive(g->parent) &&
        poll(&p,1,0)>=0 && !(p.revents&(POLLRDHUP|POLLHUP|POLLERR|POLLNVAL)) && same_boundary(g);
}
static uint64_t state(struct launcher *g) {
    uint64_t flags=g->child>0?1:0;
    if(g->child>0 && !g->reaped){
        int status;
        pid_t result=waitpid(g->child,&status,WNOHANG);
        if(result==g->child){g->reaped=1;g->status=status;}
        else if(result<0)return UINT64_MAX;
    }
    if(g->errorfd>=0 && !g->exec_closed && !g->exec_error){
        int error=0;ssize_t n=read(g->errorfd,&error,sizeof(error));
        if(n==0)g->exec_closed=1;
        else if(n>0)g->exec_error=1;
        else if(errno!=EAGAIN && errno!=EWOULDBLOCK && errno!=EINTR)g->exec_error=1;
    }
    if(g->exec_closed && !g->exec_error)flags|=2;
    if(g->child>0 && !g->reaped && alive(g->childfd))flags|=4;
    if(g->reaped)flags|=8;
    if(g->exec_error)flags|=16;
    return flags|((uint64_t)(unsigned)g->status<<32);
}
/* Phase 5 owned fault operations (thesis-lite faults): act only on the staged child this helper
 * owns, verified by pid and token like QUERY; a refusal answers FAULTED with reason 6 and changes
 * nothing. freeze/thaw write the owned cgroup's cgroup.freeze and wait briefly for cgroup.events. */
static int write_freeze(struct launcher *g,char value) {
    int fd=openat(g->cg,"cgroup.freeze",O_WRONLY|O_CLOEXEC|O_NOFOLLOW);if(fd<0)return -1;
    ssize_t n=write(fd,&value,1);close(fd);return n==1?0:-1;
}
static unsigned owned_fault(struct launcher *g,unsigned kind) {
    /* 0 done, 6 refused (nothing changed; a timed-out freeze/thaw is rolled back first),
     * 7 indeterminate (rollback failed): the caller fails closed. */
    if(g->child<=0||g->reaped||!alive(g->childfd))return 6U;
    if(kind==FAULT_KILL)return syscall(SYS_pidfd_send_signal,g->childfd,SIGKILL,NULL,0)?6U:0U;
    char value=kind==FAULT_FREEZE?'1':'0',undo=kind==FAULT_FREEZE?'0':'1';uint64_t want=kind==FAULT_FREEZE?1:0,frozen=2;
    if(write_freeze(g,value))return 6U;
    for(int i=0;i<200;i++){
        if(!field(g,"cgroup.events","frozen",&frozen)&&frozen==want)return 0U;
        struct pollfd p={.fd=g->childfd,.events=POLLIN};poll(&p,1,1);
    }
    return write_freeze(g,undo)?7U:6U;
}
static int respond(struct launcher *g,unsigned kind,unsigned reason,int transfer) {
    unsigned char p[PACKET]={0};memcpy(p,"LC09",4);p[7]=(unsigned char)kind;
    put64(p+8,g->sequence);put64(p+16,g->deadline);memcpy(p+24,g->scope,32);put64(p+56,reason);
    put64(p+64,(uint64_t)g->identity.st_dev);put64(p+72,(uint64_t)g->identity.st_ino);
    if(g->child>0){put64(p+80,(uint64_t)g->child);memcpy(p+88,g->token,32);}
    uint64_t flags=state(g);if(flags==UINT64_MAX)return -1;put64(p+120,flags);
    struct iovec iov={.iov_base=p,.iov_len=sizeof(p)};
    union{struct cmsghdr align;unsigned char data[CMSG_SPACE(sizeof(int))];} control;
    struct msghdr msg={.msg_iov=&iov,.msg_iovlen=1};
    if(transfer>=0){
        memset(&control,0,sizeof(control));msg.msg_control=control.data;msg.msg_controllen=sizeof(control.data);
        struct cmsghdr *c=CMSG_FIRSTHDR(&msg);c->cmsg_level=SOL_SOCKET;c->cmsg_type=SCM_RIGHTS;c->cmsg_len=CMSG_LEN(sizeof(int));
        memcpy(CMSG_DATA(c),&transfer,sizeof(int));
    }
    return sendmsg(g->socket,&msg,MSG_DONTWAIT|MSG_NOSIGNAL)==PACKET?0:-1;
}
static int receive(struct launcher *g,unsigned char *p) {
    union{struct cmsghdr align;unsigned char data[CMSG_SPACE(sizeof(struct ucred))+CMSG_SPACE(8*sizeof(int))];} control;
    struct iovec iov={.iov_base=p,.iov_len=PACKET};
    struct msghdr msg={.msg_iov=&iov,.msg_iovlen=1,.msg_control=control.data,.msg_controllen=sizeof(control.data)};
    ssize_t n=recvmsg(g->socket,&msg,MSG_DONTWAIT|MSG_CMSG_CLOEXEC);
    if(n<0)return (errno==EAGAIN||errno==EWOULDBLOCK||errno==EINTR)?1:-1;
    int valid=n==PACKET && !(msg.msg_flags&(MSG_TRUNC|MSG_CTRUNC));unsigned credentials=0;
    for(struct cmsghdr *c=CMSG_FIRSTHDR(&msg);c;c=CMSG_NXTHDR(&msg,c)){
        if(c->cmsg_level==SOL_SOCKET&&c->cmsg_type==SCM_RIGHTS){
            size_t bytes=c->cmsg_len>=CMSG_LEN(0)?c->cmsg_len-CMSG_LEN(0):0;
            for(size_t i=0;i+sizeof(int)<=bytes;i+=sizeof(int)){int fd;memcpy(&fd,(unsigned char*)CMSG_DATA(c)+i,sizeof(fd));close(fd);}valid=0;
        }else if(c->cmsg_level==SOL_SOCKET&&c->cmsg_type==SCM_CREDENTIALS&&c->cmsg_len==CMSG_LEN(sizeof(struct ucred))){
            struct ucred peer;memcpy(&peer,CMSG_DATA(c),sizeof(peer));
            if(peer.pid!=g->peer.pid||peer.uid!=g->peer.uid||peer.gid!=g->peer.gid)valid=0;
            ++credentials;
        }else valid=0;
    }
    return valid&&credentials==1?0:-1;
}
static char *string(struct launcher *g,size_t size,size_t *offset) {
    if(*offset>size || size-*offset<4)return NULL;
    uint32_t n=get32(g->config+*offset);*offset+=4;
    if(n>4096 || n>=size-*offset || memchr(g->config+*offset,0,n) || g->config[*offset+n]!=0)return NULL;
    char *value=(char*)g->config+*offset;*offset+=(size_t)n+1;return value;
}
static int initialize(struct launcher *g,int argc,char **argv) {
    int cg,channel,input;
    if(argc!=4||decimal(argv[1],&cg)||decimal(argv[2],&channel)||decimal(argv[3],&input)||cg==channel||cg==input||channel==input)return -1;
    g->cg=fcntl(cg,F_DUPFD_CLOEXEC,3);g->socket=fcntl(channel,F_DUPFD_CLOEXEC,3);if(g->cg<0||g->socket<0)return -1;
    struct statfs fs;struct stat info;
    int seals=fcntl(input,F_GET_SEALS);
    if(seals<0 || (seals&SEALS)!=SEALS)return -1;
    if(fstatfs(g->cg,&fs)||fs.f_type!=CGROUP2_MAGIC||fstat(g->cg,&g->identity)||!same_boundary(g)||
       fstat(input,&info)||!S_ISREG(info.st_mode)||info.st_size<CONFIG_HEADER||info.st_size>65536)return -1;
    size_t size=(size_t)info.st_size;g->config=malloc(size);if(!g->config)return -1;
    if(pread(input,g->config,size,0)!=(ssize_t)size||memcmp(g->config,"LCF9",4)||get32(g->config+4)!=1)return -1;
    g->generation=get64(g->config+8);g->deadline=g->generation;
    if(get64(g->config+16)!=(uint64_t)g->identity.st_dev||get64(g->config+24)!=(uint64_t)g->identity.st_ino)return -1;
    unsigned arguments=get32(g->config+32),environment=get32(g->config+36);
    if(!arguments||arguments>64||environment>32)return -1;
    memcpy(g->digest,g->config+40,32);
    unsigned scope_length=0;
    if(EVP_Digest(g->config,size,g->scope,&scope_length,EVP_sha256(),NULL)!=1||scope_length!=32)return -1;
    size_t offset=CONFIG_HEADER;
    for(unsigned i=0;i<arguments;++i){g->argv[i]=string(g,size,&offset);if(!g->argv[i])return -1;}
    g->directory=string(g,size,&offset);if(!g->directory)return -1;
    for(unsigned i=0;i<environment;++i){g->env[i]=string(g,size,&offset);if(!g->env[i]||!strchr(g->env[i],'=')||g->env[i][0]=='=')return -1;}
    if(offset!=size||g->argv[0][0]!='/'||g->directory[0]!='/')return -1;
    uint64_t now=now_ns();if(!now||g->generation<=now+2*NS||g->generation-now>394*NS)return -1;
    int type,pass=1;socklen_t length=sizeof(type),peer_length=sizeof(g->peer);
    if(getsockopt(g->socket,SOL_SOCKET,SO_TYPE,&type,&length)||type!=SOCK_SEQPACKET||
       getsockopt(g->socket,SOL_SOCKET,SO_PEERCRED,&g->peer,&peer_length)||peer_length!=sizeof(g->peer)||
       g->peer.pid!=getppid()||g->peer.pid<=1||g->peer.uid!=getuid()||g->peer.gid!=getgid()||
       setsockopt(g->socket,SOL_SOCKET,SO_PASSCRED,&pass,sizeof(pass)))return -1;
    g->parent=(int)syscall(SYS_pidfd_open,g->peer.pid,0);
    return g->parent>=0&&alive(g->parent)&&getppid()==g->peer.pid&&!prctl(PR_SET_DUMPABLE,0,0,0,0)&&!prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)?0:-1;
}
static int prepare_image(struct launcher *g) {
    int source=open(g->argv[0],O_RDONLY|O_CLOEXEC|O_NOFOLLOW|O_NONBLOCK);if(source<0)return -1;
    struct stat info;
    if(fstat(source,&info)||!S_ISREG(info.st_mode)||info.st_size<64||info.st_size>MAX_IMAGE||
       !(info.st_mode&0111)||(info.st_mode&(S_ISUID|S_ISGID))){close(source);return -1;}
    g->image=(int)syscall(SYS_memfd_create,"maestro-catalog-image",MFD_CLOEXEC|MFD_ALLOW_SEALING);
    EVP_MD_CTX *hash=EVP_MD_CTX_new();int okay=g->image>=0&&hash&&EVP_DigestInit_ex(hash,EVP_sha256(),NULL)==1;
    size_t total=0;unsigned char bytes[16384];
    while(okay){
        if(!enabled(g)){okay=0;break;}
        ssize_t n=read(source,bytes,sizeof(bytes));if(n<0){if(errno==EINTR)continue;okay=0;break;}if(!n)break;
        if(!total&&(n<4||memcmp(bytes,"\177ELF",4))){okay=0;break;}
        total+=(size_t)n;if(total>MAX_IMAGE||EVP_DigestUpdate(hash,bytes,(size_t)n)!=1){okay=0;break;}
        size_t used=0;
        while(used<(size_t)n){ssize_t w=write(g->image,bytes+used,(size_t)n-used);if(w<=0){okay=0;break;}used+=(size_t)w;}
    }
    close(source);unsigned char digest[EVP_MAX_MD_SIZE];unsigned length=0;
    okay=okay&&total==(size_t)info.st_size&&EVP_DigestFinal_ex(hash,digest,&length)==1&&length==32&&!memcmp(digest,g->digest,32);
    EVP_MD_CTX_free(hash);
    if(!okay||fchmod(g->image,0700)||fcntl(g->image,F_ADD_SEALS,SEALS)<0)return -1;
    g->cwd=open(g->directory,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);return g->cwd<0?-1:0;
}
static void child_exec(struct launcher *g,int errorfd) {
    int error;
    if(syscall(SYS_close_range,3U,UINT_MAX,4U)||setsid()<0||fchdir(g->cwd))goto fail;
    int null=open("/dev/null",O_RDWR|O_CLOEXEC);if(null<0)goto fail;
    for(int fd=0;fd<3;++fd)if(dup2(null,fd)<0)goto fail;
    syscall(SYS_execveat,g->image,"",g->argv,g->env,AT_EMPTY_PATH);
fail:
    error=errno;ssize_t ignored=write(errorfd,&error,sizeof(error));(void)ignored;_exit(127);
}
static int stage_child(struct launcher *g) {
    g->attempted=1;
    uint64_t frozen,populated,descendants;
    if(!enabled(g)||field(g,"cgroup.events","frozen",&frozen)||frozen!=1||
       field(g,"cgroup.events","populated",&populated)||populated||field(g,"cgroup.stat","nr_descendants",&descendants)||descendants||prepare_image(g))return -1;
    if(getrandom(g->token,32,0)!=32||!enabled(g))return -1;
    int errors[2];if(pipe2(errors,O_CLOEXEC|O_NONBLOCK))return -1;
    struct clone_args args={0};args.flags=CLONE_INTO_CGROUP|CLONE_PIDFD;args.cgroup=(__u64)(unsigned)g->cg;
    args.pidfd=(uint64_t)(uintptr_t)&g->childfd;args.exit_signal=SIGCHLD;
    long child=syscall(SYS_clone3,&args,sizeof(args));
    if(!child){close(errors[0]);child_exec(g,errors[1]);}
    close(errors[1]);g->errorfd=errors[0];
    if(child<0)return -1;
    g->child=(pid_t)child;
    if(!enabled(g)||field(g,"cgroup.events","frozen",&frozen)||frozen!=1||!alive(g->childfd))return -1;
    return 0;
}
static int cleanup(struct launcher *g) {
    if(g->child>0&&!g->reaped){
        syscall(SYS_pidfd_send_signal,g->childfd,SIGKILL,NULL,0);
        uint64_t now=now_ns(),end=g->generation;if(now&&end>now+2*NS)end=now+2*NS;
        while(now_ns()<end){
            if(state(g)==UINT64_MAX)return 70;
            if(g->reaped)return 0;
            struct pollfd p={.fd=g->childfd,.events=POLLIN};poll(&p,1,1);
        }
        return 70;
    }
    return 0;
}
int main(int argc,char **argv) {
    struct launcher g={.cg=-1,.socket=-1,.parent=-1,.childfd=-1,.errorfd=-1,.image=-1,.cwd=-1};
    if(initialize(&g,argc,argv))return 64;
    if(respond(&g,READY,0,g.cg))return cleanup(&g);
    for(;;){
        uint64_t now=now_ns();if(!now||now>=g.generation-2*NS||!alive(g.parent))return cleanup(&g);
        struct pollfd fds[2]={{.fd=g.parent,.events=POLLIN},{.fd=g.socket,.events=POLLIN|POLLRDHUP}};
        int rc=poll(fds,2,10);if(rc<0){if(errno==EINTR)continue;return cleanup(&g);}
        if(fds[0].revents||(fds[1].revents&(POLLHUP|POLLRDHUP|POLLERR|POLLNVAL)))return cleanup(&g);
        if(!(fds[1].revents&POLLIN))continue;
        unsigned char p[PACKET];if(receive(&g,p)){return cleanup(&g);}
        unsigned kind=get32(p+4);uint64_t until=get64(p+16);
        if(memcmp(p,"LC09",4)||get64(p+8)!=g.sequence+1||memcmp(p+24,g.scope,32)||get64(p+56)||
           get64(p+64)!=(uint64_t)g.identity.st_dev||get64(p+72)!=(uint64_t)g.identity.st_ino||get64(p+120)||
           until<=now_ns()||until-now_ns()>5*NS||until>g.generation-2*NS)return cleanup(&g);
        ++g.sequence;g.deadline=until;
        if(kind==STAGE){
            unsigned char zero[40]={0};
            if(g.attempted||memcmp(p+80,zero,sizeof(zero)))return cleanup(&g);
            if(stage_child(&g)){respond(&g,ERROR,3,-1);return cleanup(&g);}
            if(respond(&g,STAGED,0,g.childfd))return cleanup(&g);
        }else if(kind==QUERY||kind==CANCEL||kind==FAULT_KILL||kind==FAULT_FREEZE||kind==FAULT_THAW){
            if(get64(p+80)!=(uint64_t)g.child||memcmp(p+88,g.token,32))return cleanup(&g);
            if(kind==CANCEL){int result=cleanup(&g);respond(&g,CANCELLED,result?6U:0U,-1);return result;}
            if(kind==QUERY){if(respond(&g,OBSERVED,0,-1))return cleanup(&g);}
            else{unsigned reason=owned_fault(&g,kind);if(reason==7U||respond(&g,FAULTED,reason,-1))return cleanup(&g);}
        }else return cleanup(&g);
    }
}
