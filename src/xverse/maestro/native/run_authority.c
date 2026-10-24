/* AF17/AC17v2: original run-wide epoch/child registry. Not operator admission.
 * Exact original broker validates M3/Argus/C1 facts; this private native authority
 * owns frozen Stage, one-use Release, cancellation and original child waits.
 * S1b (design-stabilization-s1b.md): an AR17 v2 recipe may declare a TERM grace, a private capped
 * stderr file and the nonce-marker readiness probe; an AR17 v1 unit behaves exactly as before. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <linux/sched.h>
#include <openssl/crypto.h>
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
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#define NS UINT64_C(1000000000)
#define SEALS (F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL)
#define PACKET 320
#define MAX_IMAGE (32U*1024U*1024U)
enum { REGISTER=1, INTENT=2, STAGE=3, ARM=4, RELEASE=5, QUERY=6, STOP=7,
 RETIRE=8, RENEW=9, CANCEL=10, QUERY_ISSUED=11, ADVANCE=12,
 FAULT_KILL=13, FAULT_FREEZE=14, FAULT_THAW=15,
 READY=16, REGISTERED=17, INTENT_RECORDED=18, STAGED=19, ARMED=20,
 RELEASED=21, OBSERVED=22, STOPPED=23, RETIRED=24, RENEWED=25,
 CANCELLED=26, REJECTED=27, ADVANCED=28, FAULTED=29, FAULT_REFUSED=30,
 TERM=31, TERM_SENT=32 };
/* S1b state bits: term-sent, exited-on-term (requires term-sent), marker-ready (latched), stderr-truncated. */
#define TERM_BIT UINT64_C(512)
#define EXITED_BIT UINT64_C(1024)
#define MARKER_BIT UINT64_C(2048)
#define TRUNCATED_BIT UINT64_C(4096)
#define READY_DIR ".xverse-ready"
/* Phase 5 (thesis-lite faults): FAULTED answers a performed operation, FAULT_REFUSED a refused one. */
enum { NONE=0, LEASE=1, OWNER=2, CONTROL=3, PROTOCOL=4, CANCEL_REASON=5, FREEZE_FAILED=6, EXPIRED=7 };
struct generation {
 int cg,pidfd,errorfd,stderr_fd,probe; pid_t pid;
 uint64_t number,device,inode,epoch,ticket_end,cached,stop_state,retire_state;
 unsigned intent,attempted,staged,ticket_state,released,reaped,exec_closed,exec_error,retired,removed,stop_saved,retire_saved;
 unsigned term_sent,exited_on_term,marker_ready,truncated,checks;
 unsigned char proof[144],boundary[32],token[32],ticket[32];
 char nonce[64];
};
struct unit {
 unsigned registered,used;
 int image,cwd,parent,stderr_dir; char *recipe; char *argv[33],*env[65];
 uint64_t base,maximum,cwd_device,cwd_inode,stderr_device,stderr_inode;
 unsigned grace_ms,stderr_max,probe; /* AR17 v2 controls; all zero for a v1 recipe */
 unsigned char binding[32],image_hash[32],recipe_hash[32];
 struct generation history[128];
};
struct authority {
 int channel,parent; struct ucred peer;
 uint64_t generation,lease,epoch,sequence,deadline;
 unsigned count,registered,closed,freeze_failed;
 unsigned char scope[32],session[32],watch_key[32]; /* F-02 (finding 403): supervisor watch key */
 struct unit units[16];
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
/* S1b: every new descriptor is O_CLOEXEC and >= 3 (an input fd < 3 is moved up, then closed). */
static int high(int fd) {
    if(fd<0||fd>=3)return fd;
    int moved=fcntl(fd,F_DUPFD_CLOEXEC,3);close(fd);return moved;
}
static int zero(const unsigned char *p,size_t n) {
    for(size_t i=0;i<n;++i)if(p[i])return 0;
    return 1;
}
static void put32(unsigned char *p,uint32_t n) {
    for(unsigned i=0;i<4;++i){p[3-i]=(unsigned char)n;n>>=8;}
}
static int enabled(struct authority *g) {
    uint64_t now=now_ns();struct pollfd p={.fd=g->channel,.events=POLLRDHUP};
    return !g->closed&&now&&now<g->deadline&&now<g->lease&&now<g->generation-2*NS&&alive(g->parent)&&
        poll(&p,1,0)>=0&&!(p.revents&(POLLRDHUP|POLLHUP|POLLERR|POLLNVAL));
}
static int identity(int fd,uint64_t dev,uint64_t ino) {
    struct stat s;
    return !fstat(fd,&s)&&S_ISDIR(s.st_mode)&&(uint64_t)s.st_dev==dev&&(uint64_t)s.st_ino==ino;
}
static int removed(struct generation *e) {
    if(e->removed)return 1;
    struct stat s;
    if(e->cg<0||fstat(e->cg,&s)||(uint64_t)s.st_dev!=e->device||
       (uint64_t)s.st_ino!=e->inode)return 0;
    /* Kernfs link counts are not an unlink predicate. Fixed controls cannot be
     * individually removed; require their absence through the original FD. */
    const char *names[]={"cgroup.events","cgroup.procs","cgroup.freeze"};
    for(unsigned i=0;i<3;++i){
        int fd=openat(e->cg,names[i],O_RDONLY|O_NOFOLLOW|O_CLOEXEC);
        if(fd>=0){close(fd);return 0;}
        if(errno!=ENOENT)return 0;
    }
    return 1;
}
static uint64_t state(struct generation *e) {
    if(e->cg<0&&e->removed)return e->cached;
    uint64_t value=e->staged?1:0;
    if(e->pid>0&&!e->reaped){
        int status;pid_t pid;
        do{pid=waitpid(e->pid,&status,WNOHANG);}while(pid<0&&errno==EINTR);
        if(pid==e->pid)e->reaped=1;
        else if(pid<0)return UINT64_MAX;
    }
    if(e->errorfd>=0&&!e->exec_closed&&!e->exec_error){
        int error=0;ssize_t n=read(e->errorfd,&error,sizeof(error));
        if(n==0)e->exec_closed=1;
        else if(n>0||(errno!=EAGAIN&&errno!=EWOULDBLOCK&&errno!=EINTR))e->exec_error=1;
        if(e->exec_closed||e->exec_error){close(e->errorfd);e->errorfd=-1;}
    }
    if(e->exec_closed&&!e->exec_error)value|=2;
    if(e->pid>0&&!e->reaped&&alive(e->pidfd))value|=4;
    if(e->reaped)value|=8;
    if(e->exec_error)value|=16;
    uint64_t frozen,populated,descendants;
    if(e->cg>=0&&!field(e->cg,"cgroup.events","frozen",&frozen)&&frozen==1)value|=32;
    if(e->cg>=0&&!field(e->cg,"cgroup.events","populated",&populated)&&!populated&&
       !field(e->cg,"cgroup.stat","nr_descendants",&descendants)&&!descendants)value|=64;
    if(e->retired)value|=128;
    if(removed(e))value|=256;
    if(e->term_sent)value|=TERM_BIT;
    if(e->exited_on_term)value|=EXITED_BIT;
    if(e->marker_ready)value|=MARKER_BIT;
    if(e->truncated)value|=TRUNCATED_BIT;
    return value;
}
static uint64_t freeze_all(struct authority *g,uint64_t end) {
    /* F-01 (findings 394, 397): first issue the freeze write for every live generation, never skipped
     * for an elapsed budget; then one bounded wait over all pending units, each checked at least once. */
    uint64_t mask=0,pending=0;
    for(unsigned i=0;i<g->count;++i){
        struct unit *u=&g->units[i];if(!u->registered)continue;
        struct generation *e=&u->history[u->used-1];
        if(removed(e)){mask|=UINT64_C(1)<<i;continue;}
        if(write_freeze(e->cg,'1')){g->freeze_failed=1;continue;}
        pending|=UINT64_C(1)<<i;
    }
    for(;;){
        for(unsigned i=0;i<g->count;++i){
            if(!(pending&(UINT64_C(1)<<i)))continue;
            struct unit *u=&g->units[i];struct generation *e=&u->history[u->used-1];uint64_t frozen=0;
            if(!field(e->cg,"cgroup.events","frozen",&frozen)&&frozen==1){mask|=UINT64_C(1)<<i;pending&=~(UINT64_C(1)<<i);}
        }
        if(!pending||now_ns()>=end)break;
        struct pollfd p={.fd=g->parent,.events=POLLIN};poll(&p,1,1);
    }
    if(pending)g->freeze_failed=1;
    return mask;
}
static uint64_t close_authority(struct authority *g,uint64_t end) {
    if(!g->closed){g->closed=1;if(g->epoch!=UINT64_MAX)++g->epoch;}
    for(unsigned i=0;i<g->count;++i){
        struct unit *u=&g->units[i];
        for(unsigned j=0;j<u->used;++j){u->history[j].ticket_state=3;memset(u->history[j].ticket,0,32);}
    }
    return freeze_all(g,end);
}
/* F-01: closing never inherits an already-elapsed request deadline. */
static uint64_t close_end(struct authority *g) { uint64_t now=now_ns(),end=g->generation;if(now&&end>now+2*NS)end=now+2*NS;return end; }
static int send_packet(struct authority *g,unsigned char *p,int fd) {
    struct iovec iov={.iov_base=p,.iov_len=PACKET};
    union{struct cmsghdr align;unsigned char data[CMSG_SPACE(sizeof(int))];}control;
    struct msghdr message={.msg_iov=&iov,.msg_iovlen=1};
    if(fd>=0){
        memset(&control,0,sizeof(control));message.msg_control=control.data;message.msg_controllen=sizeof(control.data);
        struct cmsghdr *h=CMSG_FIRSTHDR(&message);h->cmsg_level=SOL_SOCKET;h->cmsg_type=SCM_RIGHTS;
        h->cmsg_len=CMSG_LEN(sizeof(int));memcpy(CMSG_DATA(h),&fd,sizeof(fd));
    }
    return sendmsg(g->channel,&message,MSG_DONTWAIT|MSG_NOSIGNAL)==PACKET?0:-1;
}
static int run_reply(struct authority *g,unsigned kind,uint64_t state_value,unsigned reason) {
    unsigned char p[PACKET]={0};memcpy(p,"AF17",4);put32(p+4,kind);put64(p+8,g->sequence);
    put64(p+16,g->deadline);memcpy(p+24,g->scope,32);put64(p+64,g->epoch);
    put64(p+288,state_value);put64(p+296,reason);
    if(kind==READY||kind==RENEWED)put64(p+304,g->lease);
    return send_packet(g,p,-1);
}
static int unit_reply(struct authority *g,const unsigned char *request,unsigned kind,struct generation *e,int transfer) {
    unsigned char p[PACKET];memcpy(p,request,PACKET);put32(p+4,kind);put64(p+64,g->epoch);
    uint64_t flags=(kind==STOPPED&&e->stop_saved)?e->stop_state:
        ((kind==RETIRED&&e->retire_saved)?e->retire_state:state(e));
    if(flags==UINT64_MAX)return -1;
    put64(p+288,flags);put64(p+296,0);put64(p+304,0);
    if(kind!=REGISTERED)memcpy(p+80,e->proof,144);
    if(e->staged)memcpy(p+256,e->token,32);
    if(kind==ARMED||kind==RELEASED)memcpy(p+224,e->ticket,32);
    else memset(p+224,0,32);
    return send_packet(g,p,transfer);
}
/* Phase 5 owned fault operations on the exact registered generation: kill through its pidfd,
 * freeze/thaw through its owned cgroup with cgroup.events observed. Returns 0 done, 1 refused
 * (nothing changed: a timed-out freeze/thaw is rolled back first), -1 indeterminate (the rollback
 * itself failed; the caller fails closed). */
static int owned_fault(struct generation *e,unsigned kind) {
    uint64_t flags=state(e);if(flags==UINT64_MAX||e->pid<=0||e->reaped||!(flags&4))return 1;
    if(kind==FAULT_KILL)return syscall(SYS_pidfd_send_signal,e->pidfd,SIGKILL,NULL,0)?1:0;
    char value=kind==FAULT_FREEZE?'1':'0',undo=kind==FAULT_FREEZE?'0':'1';uint64_t want=kind==FAULT_FREEZE?1:0,frozen=2;
    if(e->cg<0||write_freeze(e->cg,value))return 1;
    for(int i=0;i<200;i++){
        if(!field(e->cg,"cgroup.events","frozen",&frozen)&&frozen==want)return 0;
        struct pollfd wait={.fd=e->pidfd,.events=POLLIN};poll(&wait,1,1);
    }
    return write_freeze(e->cg,undo)?-1:1;
}
static int receive(struct authority *g,unsigned char *p,int *fds,unsigned *count) {
    union{struct cmsghdr align;unsigned char data[CMSG_SPACE(sizeof(struct ucred))+CMSG_SPACE(8*sizeof(int))];}control;
    struct iovec iov={.iov_base=p,.iov_len=PACKET};
    struct msghdr msg={.msg_iov=&iov,.msg_iovlen=1,.msg_control=control.data,.msg_controllen=sizeof(control.data)};
    ssize_t n=recvmsg(g->channel,&msg,MSG_DONTWAIT|MSG_CMSG_CLOEXEC);
    if(n<0)return(errno==EAGAIN||errno==EWOULDBLOCK||errno==EINTR)?1:-1;
    unsigned credentials=0,rights=0;int valid=n==PACKET&&!(msg.msg_flags&(MSG_TRUNC|MSG_CTRUNC));*count=0;
    for(struct cmsghdr *h=CMSG_FIRSTHDR(&msg);h;h=CMSG_NXTHDR(&msg,h)){
        if(h->cmsg_level==SOL_SOCKET&&h->cmsg_type==SCM_RIGHTS){
            size_t bytes=h->cmsg_len>=CMSG_LEN(0)?h->cmsg_len-CMSG_LEN(0):0;
            if(++rights>1||!bytes||bytes%sizeof(int))valid=0;
            for(size_t i=0;i+sizeof(int)<=bytes;i+=sizeof(int)){
                int fd;memcpy(&fd,(unsigned char*)CMSG_DATA(h)+i,sizeof(fd));
                if(*count<8)fds[(*count)++]=fd;else{close(fd);valid=0;}
            }
        }else if(h->cmsg_level==SOL_SOCKET&&h->cmsg_type==SCM_CREDENTIALS&&h->cmsg_len==CMSG_LEN(sizeof(struct ucred))){
            struct ucred peer;memcpy(&peer,CMSG_DATA(h),sizeof(peer));
            if(peer.pid!=g->peer.pid||peer.uid!=g->peer.uid||peer.gid!=g->peer.gid)valid=0;
            ++credentials;
        }else valid=0;
    }
    return valid&&credentials==1?0:-1;
}
static int utf8(const unsigned char *p,size_t size) {
    for(size_t i=0;i<size;){
        unsigned c=p[i++],n;
        if(c<128){if(!c)return -1;continue;}
        if(c>=0xc2&&c<=0xdf)n=1;
        else if(c>=0xe0&&c<=0xef)n=2;
        else if(c>=0xf0&&c<=0xf4)n=3;
        else return -1;
        if(size-i<n)return -1;
        if((c==0xe0&&p[i]<0xa0)||(c==0xed&&p[i]>=0xa0)||
           (c==0xf0&&p[i]<0x90)||(c==0xf4&&p[i]>=0x90))return -1;
        for(unsigned j=0;j<n;++j)if(p[i+j]<0x80||p[i+j]>0xbf)return -1;
        i+=n;
    }
    return 0;
}
static int recipe(struct unit *u,int fd) {
    off_t size;if(sealed(fd,65536,&size)||size<16||digest_fd(fd,(size_t)size,u->recipe_hash))return -1;
    u->recipe=malloc((size_t)size);if(!u->recipe||pread(fd,u->recipe,(size_t)size,0)!=size)return -1;
    unsigned char *p=(unsigned char*)u->recipe;
    unsigned argc=get32(p+8),envc=get32(p+12),version=get32(p+4);
    if(memcmp(p,"AR17",4)||(version!=1&&version!=2)||!argc||argc>32||envc>64)return -1;
    size_t offset=16;
    if(version==2){ /* S1b: a v2 recipe exists only when at least one control is declared */
        if(size<48)return -1;
        u->grace_ms=get32(p+16);u->stderr_max=get32(p+20);u->probe=get32(p+24);
        u->stderr_device=get64(p+32);u->stderr_inode=get64(p+40);offset=48;
        if(get32(p+28)||u->grace_ms>4000||u->stderr_max>1048576U||u->probe>1||
           (!u->grace_ms&&!u->stderr_max&&!u->probe)||
           (!u->stderr_max)!=(!u->stderr_device)||(!u->stderr_max)!=(!u->stderr_inode))return -1;
    }
    for(unsigned i=0;i<argc+envc;++i){
        if(offset>(size_t)size||(size_t)size-offset<4)return -1;
        uint32_t length=get32(p+offset);offset+=4;
        if(length>4096||length>=(size_t)size-offset||p[offset+length]||utf8(p+offset,length)||(!i&&!length))return -1;
        char *word=(char*)p+offset;offset+=(size_t)length+1;
        if(i<argc)u->argv[i]=word;
        else{
            char *equal=strchr(word,'=');if(!equal||equal==word)return -1;
            for(char *k=word;k<equal;++k)if(!((*k>='A'&&*k<='Z')||(*k>='a'&&*k<='z')||*k=='_'||(k>word&&*k>='0'&&*k<='9')))return -1;
            size_t key=(size_t)(equal-word);
            for(unsigned j=0;j<i-argc;++j){char *other=strchr(u->env[j],'=');if((size_t)(other-u->env[j])==key&&!memcmp(u->env[j],word,key))return -1;}
            u->env[i-argc]=word;
        }
    }
    return offset==(size_t)size?0:-1;
}
static int initialize(struct authority *g,int argc,char **argv) {
    if(argc!=4)return -1;
    int channel=decimal(argv[1]),input=decimal(argv[2]),key=decimal(argv[3]);off_t size,key_size;
    if(channel<0||input<0||key<0||channel==input||key==channel||key==input||sealed(input,2688,&size)||size<288)return -1;
    /* F-02: the supervisor-generated watch key arrives only in this sealed memfd. */
    if(sealed(key,32,&key_size)||key_size!=32||pread(key,g->watch_key,32,0)!=32||zero(g->watch_key,32))return -1;
    close(key);
    unsigned char data[2688];if(pread(input,data,(size_t)size,0)!=size)return -1;
    if(memcmp(data,"AC17",4)||get32(data+4)!=2||!zero(data+104,24))return -1;
    g->generation=get64(data+8);g->lease=get64(data+16);g->deadline=g->lease;g->epoch=get64(data+24);
    uint64_t count=get64(data+32),now=now_ns();
    if(count<1||count>16||(uint64_t)size!=128+160*count||!now||g->generation<=now+2*NS||g->generation-now>394*NS||
       g->lease<=now||g->lease-now>5*NS||g->lease>g->generation-2*NS||zero(data+40,32)||zero(data+72,32))return -1;
    g->count=(unsigned)count;memcpy(g->scope,data+40,32);memcpy(g->session,data+72,32);
    uint64_t total=0;
    for(unsigned i=0;i<g->count;++i){
        const unsigned char *p=data+128+160*i;struct unit *u=&g->units[i];struct generation *e=&u->history[0];
        if(zero(p,32)||zero(p+32,32)||zero(p+64,32)||!get64(p+104)||!get64(p+120)||!zero(p+144,16))return -1;
        memcpy(u->binding,p,32);memcpy(u->image_hash,p+32,32);memcpy(u->recipe_hash,p+64,32);
        e->device=get64(p+96);e->inode=get64(p+104);u->cwd_device=get64(p+112);u->cwd_inode=get64(p+120);
        u->base=e->number=get64(p+128);u->maximum=get64(p+136);e->epoch=g->epoch;u->used=1;
        if(!u->base||u->maximum<u->base||u->maximum-u->base>127)return -1;
        total+=u->maximum-u->base+1;if(total>128)return -1;
        for(unsigned j=0;j<i;++j)if(!memcmp(u->binding,g->units[j].binding,32)||
          (e->device==g->units[j].history[0].device&&e->inode==g->units[j].history[0].inode))return -1;
    }
    if(g->epoch>UINT64_MAX-(total-g->count+1))return -1;
    g->channel=fcntl(channel,F_DUPFD_CLOEXEC,3);if(g->channel<0)return -1;
    int type,pass=1;socklen_t length=sizeof(type),peer_length=sizeof(g->peer);
    if(getsockopt(g->channel,SOL_SOCKET,SO_TYPE,&type,&length)||type!=SOCK_SEQPACKET||
       getsockopt(g->channel,SOL_SOCKET,SO_PEERCRED,&g->peer,&peer_length)||peer_length!=sizeof(g->peer)||
       g->peer.pid!=getppid()||g->peer.pid<=1||g->peer.uid!=getuid()||g->peer.gid!=getgid()||
       setsockopt(g->channel,SOL_SOCKET,SO_PASSCRED,&pass,sizeof(pass)))return -1;
    g->parent=(int)syscall(SYS_pidfd_open,g->peer.pid,0);
    return g->parent>=0&&alive(g->parent)&&getppid()==g->peer.pid&&!prctl(PR_SET_DUMPABLE,0,0,0,0)&&
        !prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)?0:-1;
}
static int register_unit(struct authority *g,struct unit *u,const unsigned char *p,int *fds,unsigned count) {
    struct generation *e=&u->history[0];struct stat image;
    off_t image_size;
    if(u->registered||!enabled(g)||get64(p+72)!=e->number||!zero(p+80,16)||
       memcmp(p+96,u->binding,32)||memcmp(p+128,u->image_hash,32)||memcmp(p+160,u->recipe_hash,32)||
       zero(p+192,32)||!zero(p+224,64)||!identity(fds[0],e->device,e->inode)||cgroup(fds[0],1)||
       !identity(fds[2],u->cwd_device,u->cwd_inode)||sealed(fds[1],MAX_IMAGE,&image_size)||image_size<64||
       fstat(fds[1],&image)||(image.st_mode&(S_ISUID|S_ISGID))||digest_fd(fds[1],(size_t)image_size,u->image_hash))return -1;
    unsigned char elf[4];if(pread(fds[1],elf,4,0)!=4||memcmp(elf,"\177ELF",4)||recipe(u,fds[3])||!enabled(g))return -1;
    /* S1b: the fifth fd is the private stderr directory, exactly when the sealed recipe declares stderr. */
    if(count!=(u->stderr_max?5U:4U))return -1;
    if(u->stderr_max){struct stat d;
        if(!identity(fds[4],u->stderr_device,u->stderr_inode)||fstat(fds[4],&d)||d.st_uid!=getuid()||(d.st_mode&077))return -1;
        u->stderr_dir=fcntl(fds[4],F_DUPFD_CLOEXEC,3);if(u->stderr_dir<0)return -1;}
    e->cg=fcntl(fds[0],F_DUPFD_CLOEXEC,3);u->image=fcntl(fds[1],F_DUPFD_CLOEXEC,3);u->cwd=fcntl(fds[2],F_DUPFD_CLOEXEC,3);
    u->parent=high(openat(fds[0],"..",O_RDONLY|O_DIRECTORY|O_CLOEXEC|O_NOFOLLOW));
    if(e->cg<0||u->image<0||u->cwd<0||u->parent<0)return -1;
    memcpy(e->boundary,p+192,32);u->registered=1;++g->registered;
    return unit_reply(g,p,REGISTERED,e,-1);
}
static int fresh(struct authority *g,const unsigned char *p) {
    for(unsigned i=0;i<g->count;++i){struct unit *u=&g->units[i];
        for(unsigned j=0;j<u->used;++j){struct generation *e=&u->history[j];
            if(e->intent&&(!memcmp(p+80,e->proof,16)||!memcmp(p+128,e->proof+48,32)||!memcmp(p+160,e->proof+80,32)))return 0;
        }
    }
    return !zero(p+80,16)&&!zero(p+96,32)&&!zero(p+128,32)&&!zero(p+160,32)&&!zero(p+192,32);
}
static void child_exec(struct unit *u,struct generation *e,int errorfd) {
    int error;
    if(syscall(SYS_close_range,3U,UINT_MAX,4U)||setsid()<0||fchdir(u->cwd))goto fail;
    int null=open("/dev/null",O_RDWR|O_CLOEXEC);if(null<0)goto fail;
    /* S1b: fds 0 and 1 stay /dev/null; fd 2 is /dev/null or the declared private stderr file. */
    for(int fd=0;fd<3;++fd)if(dup2(fd==2&&e->stderr_fd>=0?e->stderr_fd:null,fd)<0)goto fail;
    if(u->grace_ms){ /* S1b: a declared grace makes SIGTERM deliverable with its default action */
        struct sigaction action;memset(&action,0,sizeof(action));action.sa_handler=SIG_DFL;sigset_t term;
        if(sigemptyset(&action.sa_mask)||sigaction(SIGTERM,&action,NULL)||sigemptyset(&term)||
           sigaddset(&term,SIGTERM)||sigprocmask(SIG_UNBLOCK,&term,NULL))goto fail;
    }
    syscall(SYS_execveat,u->image,"",u->argv,u->env,AT_EMPTY_PATH);
fail:
    error=errno;ssize_t ignored=write(errorfd,&error,sizeof(error));(void)ignored;_exit(127);
}
/* S1b (FR-010): STAGE creates stderr-g<N> exclusively, without following links, in the sealed directory. */
static int stage_stderr(struct unit *u,struct generation *e) {
    if(!u->stderr_max)return 0;
    char name[32];if(!identity(u->stderr_dir,u->stderr_device,u->stderr_inode)||
       snprintf(name,sizeof(name),"stderr-g%llu",(unsigned long long)e->number)>=(int)sizeof(name))return -1;
    e->stderr_fd=high(openat(u->stderr_dir,name,O_WRONLY|O_APPEND|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600));
    return e->stderr_fd<0?-1:0;
}
/* S1b (FR-011): the per-generation challenge, created before clone3 while no unit process can act. */
static int stage_probe(struct unit *u,struct generation *e) {
    if(!u->probe)return 0;
    if(e->number>u->base){char aside[48];
        if(snprintf(aside,sizeof(aside),READY_DIR ".g%llu",(unsigned long long)(e->number-1))>=(int)sizeof(aside)||
           (syscall(SYS_renameat2,u->cwd,READY_DIR,u->cwd,aside,RENAME_NOREPLACE)&&errno!=ENOENT))return -1;
    }
    struct stat s;unsigned char random[32];static const char hex[]="0123456789abcdef";
    if(mkdirat(u->cwd,READY_DIR,0700))return -1;
    e->probe=high(openat(u->cwd,READY_DIR,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC));
    if(e->probe<0||fstat(e->probe,&s)||!S_ISDIR(s.st_mode)||s.st_uid!=getuid()||(s.st_mode&07777)!=0700||
       getrandom(random,32,GRND_NONBLOCK)!=32)return -1;
    for(unsigned i=0;i<32;++i){e->nonce[2*i]=hex[random[i]>>4];e->nonce[2*i+1]=hex[random[i]&15];}
    OPENSSL_cleanse(random,32);
    int fd=high(openat(e->probe,"challenge",O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0400));if(fd<0)return -1;
    ssize_t n=write(fd,e->nonce,64);return close(fd)||n!=64?-1:0;
}
/* S1b: a bounded marker check on QUERY; a FIFO, a symlink or a wrong-sized file never blocks or matches. */
static void check_marker(struct authority *g,struct unit *u,struct generation *e) {
    if(!u->probe||e->probe<0||e->marker_ready||e->checks>=3||!enabled(g)||!e->released||e->retired||
       e!=&u->history[u->used-1])return;
    ++e->checks;
    int fd=openat(e->probe,"ready",O_RDONLY|O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC);if(fd<0)return;
    struct stat s;char data[65];
    if(!fstat(fd,&s)&&S_ISREG(s.st_mode)&&s.st_size==64&&pread(fd,data,sizeof(data),0)==64&&
       !CRYPTO_memcmp(data,e->nonce,64))e->marker_ready=1;
    close(fd);
}
/* S1b: with no writer left, a declared stderr file is cut to its cap (bit 4096 records a cut). */
static int cap_stderr(struct unit *u,struct generation *e) {
    if(e->stderr_fd<0)return 0;
    struct stat s;if(fstat(e->stderr_fd,&s)||!S_ISREG(s.st_mode))return -1;
    if(s.st_size>(off_t)u->stderr_max){if(ftruncate(e->stderr_fd,(off_t)u->stderr_max))return -1;e->truncated=1;}
    close(e->stderr_fd);e->stderr_fd=-1;return 0;
}
static int stage_child(struct authority *g,struct unit *u,struct generation *e) {
    if(e->attempted||!enabled(g)||e->epoch!=g->epoch||!identity(e->cg,e->device,e->inode)||cgroup(e->cg,1)||
       !identity(u->cwd,u->cwd_device,u->cwd_inode)||getrandom(e->token,32,GRND_NONBLOCK)!=32||zero(e->token,32))return -1;
    e->attempted=1;
    if(stage_stderr(u,e)||stage_probe(u,e))return -1;
    int errors[2];if(pipe2(errors,O_CLOEXEC|O_NONBLOCK))return -1;
    struct clone_args args={0};args.flags=CLONE_INTO_CGROUP|CLONE_PIDFD;args.cgroup=(__u64)(unsigned)e->cg;
    args.pidfd=(uint64_t)(uintptr_t)&e->pidfd;args.exit_signal=SIGCHLD;
    if(!enabled(g)){close(errors[0]);close(errors[1]);return -1;}
    long child=syscall(SYS_clone3,&args,sizeof(args));
    if(child==0){close(errors[0]);child_exec(u,e,errors[1]);}
    close(errors[1]);e->errorfd=errors[0];
    if(child<0)return -1;
    e->pid=(pid_t)child;e->staged=1;
    return enabled(g)&&!cgroup(e->cg,0)&&alive(e->pidfd)?0:-1;
}
static int stop_child(struct authority *g,struct unit *u,struct generation *e) {
    if(e->retired)return 0;
    if(!e->staged||now_ns()>=g->deadline||!identity(e->cg,e->device,e->inode))return -1;
    if(e->term_sent&&!e->exited_on_term){ /* S1b: exited on TERM only if reaped and empty before the freeze */
        uint64_t flags=state(e);if(flags==UINT64_MAX)return -1;
        if((flags&(8|64))==(8|64))e->exited_on_term=1;
    }
    if(write_freeze(e->cg,'1'))return -1;
    int fd=openat(e->cg,"cgroup.kill",O_WRONLY|O_CLOEXEC|O_NOFOLLOW);if(fd<0)return -1;
    ssize_t count=write(fd,"1",1);close(fd);if(count!=1)return -1;
    while(now_ns()<g->deadline){
        uint64_t flags=state(e);if(flags==UINT64_MAX)return -1;
        if((flags&(8|32|64))==(8|32|64)){
            if(cap_stderr(u,e))return -1;
            if(e->probe>=0){close(e->probe);e->probe=-1;}
            return 0;
        }
        struct pollfd wait={.fd=e->pidfd,.events=POLLIN};poll(&wait,1,1);
    }
    return -1;
}
/* S1b (FR-009): SIGTERM through the pidfd to the leader only; idempotent; a refusal changes nothing. */
static int term_child(struct authority *g,struct generation *e) {
    if(e->term_sent)return 0;
    uint64_t flags=state(e);if(flags==UINT64_MAX)return -1;
    if(!enabled(g)||!e->released||e->retired||e->stop_saved||e->pid<=0||e->reaped||!(flags&4)||(flags&32))return 0;
    if(!syscall(SYS_pidfd_send_signal,e->pidfd,SIGTERM,NULL,0))e->term_sent=1;
    return 0;
}
/* F-02 (finding 403): ADVANCE carries the supervisor's WATCH token for its boundary in the ticket field. */
static int watched(struct authority *g,const struct stat *st,const unsigned char *token) {
    unsigned char message[20],expected[32];unsigned length=0;
    memcpy(message,"MLWT",4);put64(message+4,(uint64_t)st->st_dev);put64(message+12,(uint64_t)st->st_ino);
    int ok=HMAC(EVP_sha256(),g->watch_key,32,message,sizeof(message),expected,&length)&&length==32&&!CRYPTO_memcmp(expected,token,32);
    OPENSSL_cleanse(expected,32);return ok;
}
static int advance_unit(struct authority *g,struct unit *u,const unsigned char *p,int fd) {
    struct generation *old=&u->history[u->used-1];struct stat next;
    if(!enabled(g)||old->number==UINT64_MAX||get64(p+72)!=old->number+1||get64(p+72)>u->maximum||
       u->used>=128||g->epoch>=UINT64_MAX-1||!old->retired||!old->reaped||!removed(old)||memcmp(p+96,old->proof+16,32)||
       !fresh(g,p)||zero(p+224,32)||!zero(p+256,32)||cgroup(fd,1)||fstat(fd,&next)||!watched(g,&next,p+224))return -1;
    int parent=openat(fd,"..",O_RDONLY|O_DIRECTORY|O_CLOEXEC|O_NOFOLLOW);
    int valid=parent>=0&&same(parent,u->parent);if(parent>=0)close(parent);if(!valid)return -1;
    for(unsigned i=0;i<g->count;++i){struct unit *other=&g->units[i];
        for(unsigned j=0;j<other->used;++j)if((uint64_t)next.st_dev==other->history[j].device&&
            (uint64_t)next.st_ino==other->history[j].inode)return -1;
    }
    int duplicate=fcntl(fd,F_DUPFD_CLOEXEC,3);if(duplicate<0||!enabled(g)){if(duplicate>=0)close(duplicate);return -1;}
    uint64_t prior=state(old);if(prior==UINT64_MAX){close(duplicate);return -1;}
    old->removed=1;old->cached=(prior|256|128|8|64)&~UINT64_C(4);close(old->cg);old->cg=-1;
    ++g->epoch;
    for(unsigned i=0;i<g->count;++i){struct unit *other=&g->units[i];
        for(unsigned j=0;j<other->used;++j)if(other->history[j].ticket_state==1){other->history[j].ticket_state=3;memset(other->history[j].ticket,0,32);}
    }
    struct generation *e=&u->history[u->used++];e->cg=duplicate;e->number=get64(p+72);e->device=(uint64_t)next.st_dev;e->inode=(uint64_t)next.st_ino;
    e->epoch=g->epoch;e->intent=1;memcpy(e->proof,p+80,144);memcpy(e->boundary,p+192,32);
    return unit_reply(g,p,ADVANCED,e,-1);
}
static int command(struct authority *g,const unsigned char *p,int *fds,unsigned count) {
    unsigned kind=get32(p+4);uint64_t slot=get64(p+56),generation=get64(p+72);
    if(kind==CANCEL){
        if(count||slot||generation||!zero(p+80,208)||get64(p+304))return -1;
        uint64_t frozen=close_authority(g,close_end(g));
        return run_reply(g,CANCELLED,frozen,g->freeze_failed?FREEZE_FAILED:CANCEL_REASON);
    }
    if(kind==RENEW){
        uint64_t end=get64(p+304),now=now_ns();
        if(count||slot||generation||!zero(p+80,208)||!enabled(g)||end<=g->lease||end<=now||end-now>5*NS||end>g->generation-2*NS)return -1;
        g->lease=end;return run_reply(g,RENEWED,0,0);
    }
    if(!slot||slot>g->count||get64(p+304))return -1;
    struct unit *u=&g->units[slot-1];
    if(kind==REGISTER)return !g->closed&&(count==4||count==5)?register_unit(g,u,p,fds,count):-1;
    if(!u->registered||g->registered!=g->count)return -1;
    if(kind==ADVANCE)return count==1?advance_unit(g,u,p,fds[0]):-1;
    if(count)return -1;
    struct generation *e=NULL;
    for(unsigned j=0;j<u->used;++j)if(u->history[j].number==generation){e=&u->history[j];break;}
    if(!e)return -1;
    if(kind==INTENT){
        if(!enabled(g)||e!=&u->history[u->used-1]||e->intent||!fresh(g,p)||
           memcmp(p+192,e->boundary,32)||!zero(p+224,64)||cgroup(e->cg,1))return -1;
        e->intent=1;e->epoch=g->epoch;memcpy(e->proof,p+80,144);
        return unit_reply(g,p,INTENT_RECORDED,e,-1);
    }
    if(!e->intent||memcmp(p+80,e->proof,144))return -1;
    if(kind==STAGE){
        if(!zero(p+224,64)||stage_child(g,u,e))return -1;
        return unit_reply(g,p,STAGED,e,e->pidfd);
    }
    if(kind==QUERY_ISSUED){
        if(!zero(p+224,64)||!e->staged)return -1;
        return unit_reply(g,p,STAGED,e,e->pidfd);
    }
    if(!e->staged||memcmp(p+256,e->token,32))return -1;
    if(kind==ARM){
        if(!zero(p+224,32)||!enabled(g)||e->epoch!=g->epoch||e->ticket_state||e->released||e->retired||
           cgroup(e->cg,0)||!alive(e->pidfd)||getrandom(e->ticket,32,GRND_NONBLOCK)!=32||zero(e->ticket,32))return -1;
        e->ticket_state=1;e->ticket_end=g->deadline;
        return unit_reply(g,p,ARMED,e,-1);
    }
    if(kind==RELEASE){
        if(!enabled(g)||e->epoch!=g->epoch||e->ticket_state!=1||e->retired||e->released||
           zero(p+224,32)||memcmp(p+224,e->ticket,32)||g->deadline>e->ticket_end||now_ns()>=e->ticket_end||cgroup(e->cg,0)||!alive(e->pidfd))return -1;
        if(!enabled(g))return -1;
        e->ticket_state=2;e->released=1; /* sole run-authority Release linearization */
        if(write_freeze(e->cg,'0'))return -1;
        while(enabled(g)&&now_ns()<e->ticket_end){
            uint64_t flags=state(e);if(flags==UINT64_MAX||flags&16)return -1;
            if(flags&2)return unit_reply(g,p,RELEASED,e,-1);
            struct pollfd wait={.fd=e->pidfd,.events=POLLIN};poll(&wait,1,1);
        }
        return -1;
    }
    if(!zero(p+224,32))return -1;
    if(kind==QUERY){check_marker(g,u,e);return unit_reply(g,p,OBSERVED,e,-1);}
    if(kind==TERM){ /* undeclared grace or a superseded generation is a protocol error */
        if(!u->grace_ms||e!=&u->history[u->used-1]||term_child(g,e))return -1;
        return unit_reply(g,p,TERM_SENT,e,-1);
    }
    if(kind==FAULT_KILL||kind==FAULT_FREEZE||kind==FAULT_THAW){
        /* Only a released, unretired latest generation of an open authority may be faulted. */
        if(!enabled(g)||g->closed||!e->released||e->retired||e!=&u->history[u->used-1])return unit_reply(g,p,FAULT_REFUSED,e,-1);
        int result=owned_fault(e,kind);if(result<0)return -1;
        return unit_reply(g,p,result?FAULT_REFUSED:FAULTED,e,-1);
    }
    if(kind==STOP){
        if(!e->stop_saved){
            if(stop_child(g,u,e))return -1;
            e->stop_state=state(e);if(e->stop_state==UINT64_MAX)return -1;
            e->stop_saved=1;
        }
        return unit_reply(g,p,STOPPED,e,-1);
    }
    if(kind==RETIRE){
        if(!e->retired){
            uint64_t flags=state(e);if(flags==UINT64_MAX||(flags&(8|32|64))!=(8|32|64))return -1;
            e->retired=1;e->ticket_state=3;memset(e->ticket,0,32);
            e->retire_state=state(e);if(e->retire_state==UINT64_MAX)return -1;
            e->retire_saved=1;
        }
        return unit_reply(g,p,RETIRED,e,-1);
    }
    return -1;
}
static int cleanup(struct authority *g) {
    uint64_t now=now_ns(),end=g->generation;if(now&&end>now+2*NS)end=now+2*NS;
    close_authority(g,end);int unresolved=g->freeze_failed;
    for(unsigned i=0;i<g->count;++i){struct unit *u=&g->units[i];
        for(unsigned j=0;j<u->used;++j){struct generation *e=&u->history[j];
            if(e->staged&&!e->reaped&&now_ns()<g->generation){
                if(e->cg>=0&&!removed(e)){
                    int fd=openat(e->cg,"cgroup.kill",O_WRONLY|O_CLOEXEC|O_NOFOLLOW);
                    if(fd>=0){ssize_t n=write(fd,"1",1);close(fd);if(n!=1)unresolved=1;}else unresolved=1;
                }
                if(syscall(SYS_pidfd_send_signal,e->pidfd,SIGKILL,NULL,0)&&errno!=ESRCH)unresolved=1;
            }
        }
    }
    for(unsigned i=0;i<g->count;++i){struct unit *u=&g->units[i];
        for(unsigned j=0;j<u->used;++j){struct generation *e=&u->history[j];
            while(e->staged&&!e->reaped&&now_ns()<end){
                if(state(e)==UINT64_MAX){unresolved=1;break;}
                struct pollfd wait={.fd=e->pidfd,.events=POLLIN};if(!e->reaped)poll(&wait,1,1);
            }
            if(e->staged&&!e->reaped)unresolved=1;
            /* S1b: best-effort cap once the leader is reaped and the boundary holds no writer. */
            uint64_t populated=1,descendants=1;
            if(e->stderr_fd>=0&&e->reaped&&(e->cg<0||removed(e)||(!field(e->cg,"cgroup.events","populated",&populated)&&
               !populated&&!field(e->cg,"cgroup.stat","nr_descendants",&descendants)&&!descendants)))(void)cap_stderr(u,e);
        }
    }
    return unresolved?70:0;
}
int main(int argc,char **argv) {
    /* F02R-01 (finding 406): not dumpable before any secret exists in this process. */
    if(prctl(PR_SET_DUMPABLE,0,0,0,0))return 64;
    struct authority *g=calloc(1,sizeof(*g));if(!g)return 64;
    g->channel=g->parent=-1;
    for(unsigned i=0;i<16;++i){g->units[i].image=g->units[i].cwd=g->units[i].parent=g->units[i].stderr_dir=-1;
        for(unsigned j=0;j<128;++j){struct generation *e=&g->units[i].history[j];e->cg=e->pidfd=e->errorfd=e->stderr_fd=e->probe=-1;}}
    if(initialize(g,argc,argv))return 64;
    if(run_reply(g,READY,0,0))return cleanup(g);
    for(;;){
        uint64_t now=now_ns();if(!now||now>=g->generation-2*NS||!alive(g->parent))return cleanup(g);
        if(!g->closed&&now>=g->lease){g->deadline=g->generation;close_authority(g,g->generation<now+2*NS?g->generation:now+2*NS);}
        uint64_t end=g->closed?g->generation-2*NS:g->lease;
        struct pollfd pollers[2]={{.fd=g->parent,.events=POLLIN},{.fd=g->channel,.events=POLLIN|POLLRDHUP}};
        int ready=poll(pollers,2,(int)((end-now+999999)/1000000));
        if(ready<0){if(errno==EINTR)continue;return cleanup(g);}
        if(pollers[0].revents||!alive(g->parent)||pollers[1].revents&(POLLRDHUP|POLLHUP|POLLERR|POLLNVAL))return cleanup(g);
        if(!(pollers[1].revents&POLLIN))continue;
        unsigned char p[PACKET];int fds[8];unsigned count=0;
        int received=receive(g,p,fds,&count);
        if(received==1)continue;
        now=now_ns();unsigned kind=received?0:get32(p+4);uint64_t until=received?0:get64(p+16);
        int valid=!received&&!memcmp(p,"AF17",4)&&((kind>=1&&kind<=15)||kind==TERM)&&
            !memcmp(p+24,g->scope,32)&&get64(p+8)==g->sequence+1&&g->sequence<8192&&
            get64(p+64)==g->epoch&&zero(p+288,16)&&zero(p+312,8)&&
            until>now&&until-now<=5*NS&&until<=g->generation-2*NS&&(g->closed||until<=g->lease);
        int result=-1;
        if(valid){g->sequence=get64(p+8);g->deadline=until;result=command(g,p,fds,count);}
        for(unsigned i=0;i<count;++i)close(fds[i]);
        if(!valid)return cleanup(g);
        if(result){close_authority(g,close_end(g));if(run_reply(g,REJECTED,0,g->freeze_failed?FREEZE_FAILED:PROTOCOL))return cleanup(g);}
    }
}
