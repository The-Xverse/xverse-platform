/* Fixed kernel component fixture. No command, shell, exec or provider input. */
#define _GNU_SOURCE
#include <errno.h>
#include <linux/sched.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 4) return 2;
    int cgfd = atoi(argv[1]), marker = atoi(argv[2]);
    int descendant = strcmp(argv[3], "descendant") == 0;
    if (!descendant && strcmp(argv[3], "single") != 0) return 2;
    int childfd = -1;
    struct clone_args args = {0};
    args.flags = CLONE_INTO_CGROUP | CLONE_PIDFD;
    args.cgroup = (uint64_t)cgfd;
    args.pidfd = (uint64_t)(uintptr_t)&childfd;
    args.exit_signal = SIGCHLD;
    long child = syscall(SYS_clone3, &args, sizeof(args));
    if (child < 0) { printf("ERROR %d\n", errno); return 77; }
    if (child == 0) {
        close(cgfd);
        if (write(marker, "M", 1) != 1) _exit(3);
        if (descendant) {
            pid_t grandchild = fork();
            if (grandchild < 0) _exit(4);
            if (grandchild > 0) _exit(0);
            if (write(marker, "D", 1) != 1) _exit(5);
        }
        for (;;) pause();
    }
    printf("CHILD %ld\n", child);
    fflush(stdout);
    int status;
    while (waitpid((pid_t)child, &status, 0) < 0) {
        if (errno != EINTR) return 6;
    }
    close(childfd);
    return 0;
}
