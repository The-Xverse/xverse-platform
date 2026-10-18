/* Default: freeze-only LG05. Explicit MAESTRO_RELEASE_GATE=1: RG06 ticket gate.
 * See unit-specification-{leaseguard5,releasegate6}.md. Neither creates children,
 * grants C1, validates operator approval or fabricates lifecycle outcomes. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <poll.h>
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
#include <sys/un.h>
#include <time.h>
#include <unistd.h>

#ifdef MAESTRO_BOUNDARY_ACK
#if MAESTRO_BOUNDARY_ACK != 1 || !defined(MAESTRO_RELEASE_GATE)
#error "Boundary ACK requires explicit MAESTRO_RELEASE_GATE=1 and MAESTRO_BOUNDARY_ACK=1"
#endif
#endif

#define NS UINT64_C(1000000000)
#ifdef MAESTRO_RELEASE_GATE
#if MAESTRO_RELEASE_GATE != 1
#error "Only explicit MAESTRO_RELEASE_GATE=1 is supported"
#endif
#define PACKET 256
#define MAGIC "RG06"
#define ARGUMENTS 8
#else
#define PACKET 64
#define MAGIC "LG05"
#define ARGUMENTS 7
#endif
#define CGROUP2_MAGIC 0x63677270

enum { RENEW=1, CANCEL=2, READY=16, RENEWED=17, FROZEN=18, UNRESOLVED=19 };
#ifdef MAESTRO_RELEASE_GATE
enum { ARM=3, RELEASE=4, ARMED=20, RELEASED=21 };
#endif
enum { NONE=0, LEASE=1, OWNER=2, CONTROL=3, PROTOCOL=4, CANCELLED=5,
       FREEZE_FAILED=6, AUTHORITY_EXPIRED=7 };

struct guard {
    int cg, socket, owner;
    struct stat identity;
    struct ucred peer;
    uint64_t generation, lease, reserve, sequence;
    unsigned char scope[32];
#ifdef MAESTRO_RELEASE_GATE
    int release_fd, ticket_state;
    uint64_t epoch, ticket_deadline;
    unsigned char ticket[160];
#endif
};

static uint64_t now_ns(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0 || ts.tv_sec < 0) return 0;
    return (uint64_t)ts.tv_sec * NS + (uint64_t)ts.tv_nsec;
}

static int decimal(const char *s, uint64_t *out) {
    uint64_t n = 0;
    if (!*s || strlen(s) > 20) return -1;
    for (; *s; ++s) {
        if (*s < '0' || *s > '9') return -1;
        unsigned digit=(unsigned)(*s-'0');
        if (n > (UINT64_MAX-digit)/10) return -1;
        n = n*10 + digit;
    }
    *out = n;
    return 0;
}

static uint64_t get64(const unsigned char *p) {
    uint64_t n = 0;
    for (unsigned i=0; i<8; ++i) n = (n<<8) | p[i];
    return n;
}

static void put64(unsigned char *p, uint64_t n) {
    for (unsigned i=0; i<8; ++i) { p[7-i]=(unsigned char)n; n >>= 8; }
}

static int respond(struct guard *g, unsigned kind, unsigned reason) {
    unsigned char p[PACKET] = {0};
    memcpy(p,MAGIC,4);
    p[7]=(unsigned char)kind;
    put64(p+8,g->sequence); put64(p+16,g->lease);
    memcpy(p+24,g->scope,32); put64(p+56,reason);
#ifdef MAESTRO_RELEASE_GATE
    put64(p+64,g->epoch);
    if (kind==ARMED || kind==RELEASED) {
        put64(p+16,g->ticket_deadline);
        memcpy(p+72,g->ticket,sizeof(g->ticket));
    }
#endif
#ifdef MAESTRO_BOUNDARY_ACK
    if (kind==READY) {
        union { struct cmsghdr alignment; unsigned char data[CMSG_SPACE(sizeof(int))]; } control;
        memset(&control,0,sizeof(control));
        struct iovec iov={ .iov_base=p, .iov_len=sizeof(p) };
        struct msghdr msg={ .msg_iov=&iov, .msg_iovlen=1,
                           .msg_control=control.data, .msg_controllen=sizeof(control.data) };
        struct cmsghdr *c=CMSG_FIRSTHDR(&msg);
        c->cmsg_level=SOL_SOCKET; c->cmsg_type=SCM_RIGHTS; c->cmsg_len=CMSG_LEN(sizeof(int));
        memcpy(CMSG_DATA(c),&g->cg,sizeof(int));
        return sendmsg(g->socket,&msg,MSG_DONTWAIT|MSG_NOSIGNAL)==PACKET ? 0 : -1;
    }
#endif
    return send(g->socket,p,sizeof(p),MSG_DONTWAIT|MSG_NOSIGNAL)==PACKET ? 0 : -1;
}

/* Fixed kernel-owned names only, no fallback path or externally supplied name. */
static int read_control(int cg, const char *name, char *data, size_t size) {
    int fd=openat(cg,name,O_RDONLY|O_NOFOLLOW|O_CLOEXEC);
    if (fd < 0) return -1;
    size_t used=0;
    for (;;) {
        ssize_t n=read(fd,data+used,size-1-used);
        if (n < 0) { close(fd); return -1; }
        if (n == 0) break;
        used+=(size_t)n;
        if (used==size-1) { close(fd); return -1; }
    }
    close(fd); data[used]=0;
    return 0;
}

static int field(int cg, const char *name, const char *key, uint64_t *out) {
    char data[4096];
    if (read_control(cg,name,data,sizeof(data))) return -1;
    int found=0;
    char *line=data;
    while (*line) {
        char *end=strchr(line,'\n');
        if (!end) return -1;
        *end=0;
        char *space=strchr(line,' ');
        if (!space || space==line || strchr(space+1,' ')) return -1;
        *space=0;
        uint64_t value;
        if (decimal(space+1,&value)) return -1;
        if (!strcmp(line,key)) {
            if (found++) return -1;
            *out=value;
        }
        line=end+1;
    }
    return found==1 ? 0 : -1;
}

static int same_boundary(struct guard *g) {
    struct stat s;
    return fstat(g->cg,&s)==0 && S_ISDIR(s.st_mode) &&
        s.st_dev==g->identity.st_dev && s.st_ino==g->identity.st_ino;
}

static int owner_alive(struct guard *g) {
    struct pollfd fd={ .fd=g->owner, .events=POLLIN };
    return poll(&fd,1,0)==0;
}

static int freeze(struct guard *g, unsigned reason) {
#ifdef MAESTRO_RELEASE_GATE
    ++g->epoch;
    g->ticket_state=3;
    memset(g->ticket,0,sizeof(g->ticket));
#endif
    uint64_t now=now_ns();
    if (!now || now >= g->generation) {
        respond(g,UNRESOLVED,AUTHORITY_EXPIRED); return 70;
    }
    uint64_t until=g->generation;
    if (g->reserve < until-now) until=now+g->reserve;
    if (!same_boundary(g)) goto fail;
    int fd=openat(g->cg,"cgroup.freeze",O_WRONLY|O_NOFOLLOW|O_CLOEXEC);
    if (fd < 0) goto fail;
    now=now_ns();
    if (!now || now>=until) { close(fd); goto fail; }
    ssize_t written=write(fd,"1",1);
    close(fd);
    if (written!=1) goto fail;
    for (;;) {
        uint64_t frozen;
        now=now_ns();
        if (!now || now>=until || !same_boundary(g)) goto fail;
        if (field(g->cg,"cgroup.events","frozen",&frozen) || frozen>1) goto fail;
        now=now_ns();
        if (!now || now>=until) goto fail;
        if (frozen) { respond(g,FROZEN,reason); return 0; }
        /* No shared Python lock; no callback or persistence in this loop. */
        struct timespec pause={ .tv_sec=0, .tv_nsec=1000000 };
        nanosleep(&pause,NULL);
    }
fail:
    respond(g,UNRESOLVED,FREEZE_FAILED); return 70;
}

static int receive(struct guard *g, unsigned char *packet) {
    union { struct cmsghdr alignment; unsigned char data[CMSG_SPACE(sizeof(struct ucred))+
                                      CMSG_SPACE(8*sizeof(int))]; } ancillary;
    struct iovec iov={ .iov_base=packet, .iov_len=PACKET };
    struct msghdr msg={ .msg_iov=&iov, .msg_iovlen=1,
                       .msg_control=ancillary.data, .msg_controllen=sizeof(ancillary.data) };
    ssize_t n=recvmsg(g->socket,&msg,MSG_DONTWAIT|MSG_CMSG_CLOEXEC);
    if (n<0 && (errno==EAGAIN || errno==EWOULDBLOCK)) return 1;
    if (n<0) return -2;
    int valid=n==PACKET && !(msg.msg_flags & (MSG_TRUNC|MSG_CTRUNC));
    unsigned credentials=0;
    for (struct cmsghdr *c=CMSG_FIRSTHDR(&msg); c; c=CMSG_NXTHDR(&msg,c)) {
        if (c->cmsg_level==SOL_SOCKET && c->cmsg_type==SCM_RIGHTS) {
            size_t bytes=c->cmsg_len>=CMSG_LEN(0) ? c->cmsg_len-CMSG_LEN(0) : 0;
            for (size_t i=0;i+sizeof(int)<=bytes;i+=sizeof(int)) {
                int fd; memcpy(&fd,(unsigned char *)CMSG_DATA(c)+i,sizeof(fd)); close(fd);
            }
            valid=0;
        } else if (c->cmsg_level==SOL_SOCKET && c->cmsg_type==SCM_CREDENTIALS &&
                   c->cmsg_len==CMSG_LEN(sizeof(struct ucred))) {
            struct ucred sender;
            memcpy(&sender,CMSG_DATA(c),sizeof(sender));
            if (++credentials!=1 || sender.pid!=g->peer.pid ||
                sender.uid!=g->peer.uid || sender.gid!=g->peer.gid) valid=0;
        } else valid=0;
    }
    if (n==0) return -2;
    return valid && credentials==1 ? 0 : -1;
}

static int initialize(struct guard *g, int argc, char **argv) {
    if (argc!=ARGUMENTS) return -1;
#ifdef MAESTRO_RELEASE_GATE
    if (decimal(argv[7],&g->epoch) || g->epoch==UINT64_MAX) return -1;
#endif
    uint64_t cg, socket;
    if (decimal(argv[1],&cg) || decimal(argv[2],&socket) || cg>INT_MAX || socket>INT_MAX ||
        cg<3 || socket<3 || cg==socket || decimal(argv[3],&g->generation) ||
        decimal(argv[4],&g->lease) || decimal(argv[5],&g->reserve)) return -1;
    if (strlen(argv[6])!=64) return -1;
    for (unsigned i=0;i<32;++i) {
        unsigned value=0;
        for (unsigned j=0;j<2;++j) {
            char c=argv[6][2*i+j];
            if (!((c>='0' && c<='9') || (c>='a' && c<='f'))) return -1;
            value=value*16+(c<='9' ? (unsigned)(c-'0') : (unsigned)(c-'a'+10));
        }
        g->scope[i]=(unsigned char)value;
    }
    g->cg=fcntl((int)cg,F_DUPFD_CLOEXEC,3);
    g->socket=fcntl((int)socket,F_DUPFD_CLOEXEC,3);
    if (g->cg<0 || g->socket<0) return -1;
    struct statfs fs;
    char type[32]; uint64_t descendants, frozen;
    if (fstatfs(g->cg,&fs) || fs.f_type!=CGROUP2_MAGIC ||
        fstat(g->cg,&g->identity) || !same_boundary(g) ||
        read_control(g->cg,"cgroup.type",type,sizeof(type)) || strcmp(type,"domain\n") ||
        field(g->cg,"cgroup.stat","nr_descendants",&descendants) || descendants ||
        field(g->cg,"cgroup.events","frozen",&frozen) || frozen!=1) return -1;
    int socket_type; socklen_t length=sizeof(socket_type);
    struct sockaddr_un address; socklen_t address_length=sizeof(address);
    socklen_t peer_length=sizeof(g->peer);
    if (getsockopt(g->socket,SOL_SOCKET,SO_TYPE,&socket_type,&length) ||
        socket_type!=SOCK_SEQPACKET ||
        getpeername(g->socket,(struct sockaddr *)&address,&address_length) ||
        address.sun_family!=AF_UNIX ||
        getsockopt(g->socket,SOL_SOCKET,SO_PEERCRED,&g->peer,&peer_length) ||
        peer_length!=sizeof(g->peer) || g->peer.pid<=1 || g->peer.pid!=getppid() ||
        g->peer.uid!=getuid() || g->peer.gid!=getgid()) return -1;
    g->owner=(int)syscall(SYS_pidfd_open,g->peer.pid,0);
    if (g->owner<0 || getppid()!=g->peer.pid || !owner_alive(g)) return -1;
    int enabled=1;
    if (setsockopt(g->socket,SOL_SOCKET,SO_PASSCRED,&enabled,sizeof(enabled)) ||
        prctl(PR_SET_DUMPABLE,0,0,0,0) || prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)) return -1;
    uint64_t now=now_ns();
    if (!now || g->reserve==0 || g->reserve>NS || g->generation<=now ||
        g->generation-now>394*NS || g->reserve>=g->generation-now ||
        g->lease<=now || g->lease-now>5*NS || g->lease>g->generation-g->reserve) return -1;
#ifdef MAESTRO_RELEASE_GATE
    g->release_fd=openat(g->cg,"cgroup.freeze",O_WRONLY|O_NOFOLLOW|O_CLOEXEC);
    if (g->release_fd<0) return -1;
#endif
    return 0;
}

#ifdef MAESTRO_RELEASE_GATE
static int zero_bytes(const unsigned char *p, size_t size) {
    unsigned char value=0;
    for (size_t i=0;i<size;++i) value|=p[i];
    return value==0;
}

static int staged_boundary(struct guard *g) {
    uint64_t frozen, populated, descendants;
    return same_boundary(g) &&
        !field(g->cg,"cgroup.events","frozen",&frozen) && frozen==1 &&
        !field(g->cg,"cgroup.events","populated",&populated) && populated==1 &&
        !field(g->cg,"cgroup.stat","nr_descendants",&descendants) && descendants==0;
}

/* One original owner loop; no command can interleave this consume/write step. */
static int ticket_command(struct guard *g, const unsigned char *p) {
    uint64_t deadline=get64(p+16), now=now_ns();
    if (!now || now>=g->lease) return freeze(g,LEASE);
    if (!owner_alive(g)) return freeze(g,OWNER);
    if (p[7]==ARM) {
        if (g->ticket_state || deadline<=now || deadline>g->lease ||
            !zero_bytes(p+200,32)) return freeze(g,PROTOCOL);
        for (unsigned offset=72;offset<200;offset+=32)
            if (zero_bytes(p+offset,32)) return freeze(g,PROTOCOL);
        if (!staged_boundary(g)) return freeze(g,PROTOCOL);
        memcpy(g->ticket,p+72,128);
        if (getrandom(g->ticket+128,32,GRND_NONBLOCK)!=32 ||
            zero_bytes(g->ticket+128,32)) return freeze(g,PROTOCOL);
        now=now_ns();
        if (!now || now>=g->lease || now>=deadline) return freeze(g,LEASE);
        if (!owner_alive(g)) return freeze(g,OWNER);
        g->ticket_state=1; g->ticket_deadline=deadline; ++g->sequence;
        if (respond(g,ARMED,NONE)) return freeze(g,CONTROL);
        return -1;
    }
    if (g->ticket_state!=1 || deadline!=g->ticket_deadline || deadline<=now ||
        memcmp(g->ticket,p+72,sizeof(g->ticket))) return freeze(g,PROTOCOL);
    if (!staged_boundary(g)) return freeze(g,PROTOCOL);
    now=now_ns();
    if (!now || now>=g->lease || now>=g->ticket_deadline) return freeze(g,LEASE);
    if (!owner_alive(g)) return freeze(g,OWNER);
    g->ticket_state=2; ++g->sequence; /* local Release linearization, ticket burned */
    memset(g->ticket+128,0,32);
    if (write(g->release_fd,"0",1)!=1) return freeze(g,FREEZE_FAILED);
    for (;;) {
        uint64_t frozen;
        now=now_ns();
        if (!now || now>=g->lease || now>=g->ticket_deadline) return freeze(g,LEASE);
        if (!owner_alive(g)) return freeze(g,OWNER);
        if (field(g->cg,"cgroup.events","frozen",&frozen) || frozen>1)
            return freeze(g,FREEZE_FAILED);
        now=now_ns();
        if (!now || now>=g->lease || now>=g->ticket_deadline) return freeze(g,LEASE);
        if (!owner_alive(g)) return freeze(g,OWNER);
        if (!frozen) break;
        struct timespec pause={ .tv_sec=0, .tv_nsec=1000000 };
        nanosleep(&pause,NULL);
    }
    if (respond(g,RELEASED,NONE)) return freeze(g,CONTROL);
    return -1;
}
#endif

int main(int argc, char **argv) {
    struct guard g={ .cg=-1, .socket=-1, .owner=-1 };
    if (initialize(&g,argc,argv)) return 64;
    if (respond(&g,READY,NONE)) return freeze(&g,CONTROL);
    for (;;) {
        uint64_t now=now_ns();
        if (!now || now>=g.lease) return freeze(&g,LEASE);
        if (!owner_alive(&g)) return freeze(&g,OWNER);
        uint64_t wait=(g.lease-now+999999)/1000000;
        struct pollfd fds[2]={{ .fd=g.owner, .events=POLLIN },
                             { .fd=g.socket, .events=POLLIN }};
        int result=poll(fds,2,(int)wait);
        if (result<0) { if (errno==EINTR) continue; return freeze(&g,CONTROL); }
        now=now_ns();
        if (!now || now>=g.lease) return freeze(&g,LEASE);
        if (fds[0].revents || !owner_alive(&g)) return freeze(&g,OWNER);
        if (fds[1].revents & (POLLHUP|POLLERR|POLLNVAL)) return freeze(&g,CONTROL);
        if (!(fds[1].revents & POLLIN)) continue;
        unsigned char p[PACKET];
        int received=receive(&g,p);
        if (received==1) continue;
        if (received) return freeze(&g,received==-2 ? CONTROL : PROTOCOL);
        now=now_ns();
        if (!now || now>=g.lease) return freeze(&g,LEASE);
        if (!owner_alive(&g)) return freeze(&g,OWNER);
        if (memcmp(p,MAGIC,4) || p[4] || p[5] || p[6] ||
            memcmp(p+24,g.scope,32) || get64(p+56) || g.sequence==UINT64_MAX ||
            get64(p+8)!=g.sequence+1)
            return freeze(&g,PROTOCOL);
#ifdef MAESTRO_RELEASE_GATE
        if (get64(p+64)!=g.epoch || !zero_bytes(p+232,24)) return freeze(&g,PROTOCOL);
        if (p[7]==ARM || p[7]==RELEASE) {
            int outcome=ticket_command(&g,p);
            if (outcome>=0) return outcome;
            continue;
        }
        if (!zero_bytes(p+72,160)) return freeze(&g,PROTOCOL);
#endif
        if (p[7]!=RENEW && p[7]!=CANCEL) return freeze(&g,PROTOCOL);
        uint64_t deadline=get64(p+16);
        if (p[7]==CANCEL) {
            if (deadline!=g.lease) return freeze(&g,PROTOCOL);
            ++g.sequence; return freeze(&g,CANCELLED);
        }
        if (deadline<=g.lease || deadline<=now || deadline-now>5*NS ||
            deadline>g.generation-g.reserve) return freeze(&g,PROTOCOL);
        now=now_ns();
        if (!now || now>=g.lease) return freeze(&g,LEASE);
        if (!owner_alive(&g)) return freeze(&g,OWNER);
        ++g.sequence; g.lease=deadline;
        if (respond(&g,RENEWED,NONE)) return freeze(&g,CONTROL);
    }
}
