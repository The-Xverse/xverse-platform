/* Owned startup-only negative control: no helper or workload births. */
#define _POSIX_C_SOURCE 200809L
#include <signal.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 3) return 2;
    int channel = atoi(argv[1]);
#ifdef STOP_READY
    if (raise(SIGSTOP) != 0) return 3;
#else
    if (send(channel, "X", 1, 0) != 1) return 4;
#endif
    (void)channel;
    for (;;) pause();
}
