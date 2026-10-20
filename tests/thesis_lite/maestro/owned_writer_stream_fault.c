/* OWNED TEST ONLY: exact public-path write/close interposition, no writer internals. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
#include "owned-writer-fault-config.h"

static int trace_fd = -1;
static unsigned armed, faults, records;

static void record(const char *operation, const char *action, size_t bytes,
                   int called, long native_result, long returned_result, int error) {
    struct timespec stamp;
    if (++records > 512U || clock_gettime(CLOCK_MONOTONIC, &stamp)) _exit(124);
    uint64_t ns = (uint64_t)stamp.tv_sec * UINT64_C(1000000000) + (uint64_t)stamp.tv_nsec;
    char line[512];
    int length = snprintf(line, sizeof(line),
        "{\"operation\":\"%s\",\"action\":\"%s\",\"observed_ns\":%llu,"
        "\"bytes\":%zu,\"native_called\":%d,\"native_result\":%ld,"
        "\"returned_result\":%ld,\"errno\":%d,\"mode\":%d}\n",
        operation, action, (unsigned long long)ns, bytes, called, native_result, returned_result, error, OWNED_MODE);
    if (length <= 0 || (size_t)length >= sizeof(line)
        || syscall(SYS_write, trace_fd, line, (size_t)length) != length) _exit(124);
}

__attribute__((constructor)) static void initialize(void) {
    trace_fd = (int)syscall(SYS_openat, AT_FDCWD, OWNED_TRACE,
        O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
    if (trace_fd < 0) _exit(125);
    record("load", "loaded", 0, 0, 0, 0, 0);
}

unsigned owned_writer_probe(void) { return UINT32_C(0x57534631); }
void owned_writer_arm(void) { armed = 1; record("arm", "armed", 0, 0, 0, 0, 0); }

static int matching(int fd) {
    int flags = fcntl(fd, F_GETFL);
    if (flags < 0 || (flags & O_ACCMODE) == O_RDONLY) return 0;
    char name[64], path[PATH_MAX];
    int length = snprintf(name, sizeof(name), "/proc/self/fd/%d", fd);
    if (length <= 0 || (size_t)length >= sizeof(name)) return 0;
    ssize_t size = readlink(name, path, sizeof(path) - 1U);
    if (size <= 0 || (size_t)size >= sizeof(path)) return 0;
    path[size] = 0;
    struct stat descriptor, target;
    return !strcmp(path, OWNED_TARGET) && !fstat(fd, &descriptor)
        && !fstatat(AT_FDCWD, OWNED_TARGET, &target, AT_SYMLINK_NOFOLLOW)
        && S_ISREG(descriptor.st_mode) && S_ISREG(target.st_mode)
        && descriptor.st_dev == target.st_dev && descriptor.st_ino == target.st_ino;
}

ssize_t write(int fd, const void *buffer, size_t count) {
    int saved = errno, selected = matching(fd);
    /* Mode1: explicit fixture seed failure, then one target flush failure. */
    if (selected && armed && (OWNED_MODE == 2 || (OWNED_MODE == 1 && faults < 2))) {
        ++faults;
        record("write", "injected-before-syscall", count, 0, 0, -1, EIO);
        errno = EIO;
        return -1;
    }
    errno = saved;
    long result = syscall(SYS_write, fd, buffer, count);
    saved = errno;
    if (selected) record("write", "passed", count, 1, result, result, result < 0 ? saved : 0);
    errno = saved;
    return (ssize_t)result;
}

int close(int fd) {
    int saved = errno, selected = matching(fd);
    errno = saved;
    long result = syscall(SYS_close, fd);
    saved = errno;
    if (selected && armed && OWNED_MODE == 3 && faults == 0 && result == 0) {
        ++faults;
        record("close", "injected-after-success", 0, 1, result, -1, EIO);
        errno = EIO;
        return -1;
    }
    if (selected) record("close", "passed", 0, 1, result, result, result < 0 ? saved : 0);
    errno = saved;
    return (int)result;
}
