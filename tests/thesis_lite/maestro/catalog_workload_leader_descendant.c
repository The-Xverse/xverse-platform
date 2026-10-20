/* Fixed owned CP12 fixture. Both leader and descendant remain in original C1. */
#define _GNU_SOURCE
#include <dirent.h>
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv) {
    if (argc != 3 || strcmp(argv[2], "single")) return 2;
    DIR *fds = opendir("/proc/self/fd");
    if (!fds) return 3;
    struct dirent *entry;
    while ((entry = readdir(fds))) {
        char *end;
        long value = strtol(entry->d_name, &end, 10);
        if (*entry->d_name && !*end && value > 2 && value != dirfd(fds)) {
            closedir(fds); return 3;
        }
    }
    closedir(fds);
    const char *visible = getenv("MAESTRO_VISIBLE");
    if (!visible || strcmp(visible, "declared") || getenv("MAESTRO_AMBIENT_SECRET")) return 4;
    int marker = open(argv[1], O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC, 0600);
    if (marker < 0 || write(marker, "EXEC\n", 5) != 5) return 5;
    pid_t child = fork();
    if (child < 0) return 6;
    if (child == 0 && write(marker, "DESCENDANT\n", 11) != 11) _exit(7);
    close(marker);
    for (;;) pause();
}
