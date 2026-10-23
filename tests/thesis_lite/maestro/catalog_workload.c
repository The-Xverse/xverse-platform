/* Exact owned executable fixture; writes evidence only under its declared cwd.
 * S1b modes (design-stabilization-s1b.md): term, ignore-term, marker, marker-late, marker-wrong,
 * marker-never, stderr-flood and streams. The marker modes answer the .xverse-ready challenge. */
#define _GNU_SOURCE
#include <fcntl.h>
#include <dirent.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>
static int marker_fd=-1;
static void on_term(int signal_number) {
    (void)signal_number;
    if(write(marker_fd,"TERM\n",5)!=5)_exit(20);
    _exit(0);
}
static void pause_ms(long ms) {
    struct timespec t={ms/1000,(ms%1000)*1000000L};while(nanosleep(&t,&t));
}
/* Answers the challenge atomically (ready.tmp, then rename); `wrong` flips one nonce character. */
static int answer(int wrong) {
    char nonce[65]={0};int in=open(".xverse-ready/challenge",O_RDONLY|O_CLOEXEC|O_NOFOLLOW);
    if(in<0)return -1;
    ssize_t n=read(in,nonce,sizeof(nonce));close(in);if(n!=64)return -1;
    if(wrong)nonce[0]=nonce[0]=='0'?'1':'0';
    int out=open(".xverse-ready/ready.tmp",O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC|O_NOFOLLOW,0600);
    if(out<0)return -1;
    n=write(out,nonce,64);if(close(out)||n!=64)return -1;
    return rename(".xverse-ready/ready.tmp",".xverse-ready/ready");
}
static int null_stream(int fd) {
    struct stat a,b;
    return !fstat(fd,&a)&&!stat("/dev/null",&b)&&S_ISCHR(a.st_mode)&&a.st_rdev==b.st_rdev;
}
int main(int argc,char **argv) {
    if(argc!=3)return 2;
    DIR *fds=opendir("/proc/self/fd");if(!fds)return 3;
    struct dirent *entry;
    while((entry=readdir(fds))){
        char *end;long value=strtol(entry->d_name,&end,10);
        if(*entry->d_name && !*end && value>2 && value!=dirfd(fds)){closedir(fds);return 3;}
    }
    closedir(fds);
    const char *visible=getenv("MAESTRO_VISIBLE");
    if(!visible||strcmp(visible,"declared")||getenv("MAESTRO_AMBIENT_SECRET"))return 4;
    int marker=open(argv[1],O_WRONLY|O_CREAT|O_APPEND|O_CLOEXEC,0600);if(marker<0)return 5;
    if(write(marker,"EXEC\n",5)!=5)return 6;
    const char *mode=argv[2];
    if(!strcmp(mode,"descendant")){
        pid_t child=fork();if(child<0)return 7;
        if(child>0)return 0;
        if(write(marker,"DESCENDANT\n",11)!=11)return 8;
    }else if(!strcmp(mode,"exit"))return 0;
    else if(!strcmp(mode,"term")){
        marker_fd=marker;struct sigaction action;memset(&action,0,sizeof(action));action.sa_handler=on_term;
        if(sigaction(SIGTERM,&action,NULL))return 10;
        for(;;)pause();
    }else if(!strcmp(mode,"ignore-term")){
        if(signal(SIGTERM,SIG_IGN)==SIG_ERR)return 11;
    }else if(!strcmp(mode,"marker")||!strcmp(mode,"marker-wrong")){
        if(answer(!strcmp(mode,"marker-wrong")))return 12;
    }else if(!strcmp(mode,"marker-late")){
        pause_ms(400);if(answer(0))return 13;
    }else if(!strcmp(mode,"stderr-flood")){
        char block[4096];memset(block,'E',sizeof(block));
        for(int i=0;i<4;++i)if(write(2,block,sizeof(block))!=(ssize_t)sizeof(block))return 14;
    }else if(!strcmp(mode,"streams")){
        struct stat err;
        if(!null_stream(0)||!null_stream(1)||fstat(2,&err))return 15;
        const char *kind=S_ISREG(err.st_mode)?"STREAMS file\n":null_stream(2)?"STREAMS null\n":"STREAMS other\n";
        if(write(marker,kind,strlen(kind))!=(ssize_t)strlen(kind)||write(2,"diagnostic\n",11)!=11)return 16;
    }else if(strcmp(mode,"single")&&strcmp(mode,"marker-never"))return 9;
    close(marker);
    for(;;)pause();
}
