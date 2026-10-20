/* Owned scope-isolation fixture; no provider, launcher or M1 admission claim. */
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
#include <time.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 4 || strcmp(argv[3], "single") != 0) return 2;
    int cgfd = atoi(argv[1]), marker = atoi(argv[2]), childfd = -1;
    struct clone_args args = {0};
    args.flags = CLONE_INTO_CGROUP | CLONE_PIDFD;
    args.cgroup = (uint64_t)cgfd;
    args.pidfd = (uint64_t)(uintptr_t)&childfd;
    args.exit_signal = SIGCHLD;
    long child = syscall(SYS_clone3, &args, sizeof(args));
    if (child < 0) { printf("ERROR %d\n", errno); return 77; }
    if (child == 0) {
        close(cgfd);
        struct timespec interval = {0, 10000000};
        /* Bounded to 45s and 4500 bytes: cannot fill the initial pipe. */
        for (int i = 0; i < 4500; ++i) {
            if (write(marker, "S", 1) != 1) _exit(3);
            nanosleep(&interval, NULL);
        }
        _exit(0);
    }
    printf("CHILD %ld\n", child);
    fflush(stdout);
    int status;
    while (waitpid((pid_t)child, &status, 0) < 0) {
        if (errno != EINTR) return 4;
    }
    close(childfd);
    return 0;
}
