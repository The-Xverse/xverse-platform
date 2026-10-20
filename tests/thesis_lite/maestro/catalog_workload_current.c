/* Owned current-generation-only output fixture, admitted before process birth. */
#define _GNU_SOURCE
#include <fcntl.h>
#include <dirent.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
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
    if(strcmp(argv[2],"single"))return 9;
    int marker=open(argv[1],O_WRONLY|O_CREAT|O_TRUNC|O_CLOEXEC,0600);if(marker<0)return 5;
    if(write(marker,"EXEC\n",5)!=5)return 6;
    close(marker);
    for(;;)pause();
}
