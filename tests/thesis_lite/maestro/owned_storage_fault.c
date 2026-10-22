/* OWNED TEST ONLY (finding 424): persistent ENOSPC from write() on one exact public path.
 * Simulates a full file system at the write call; the kernel is not called for an injected write.
 * Every other descriptor and every close passes through unchanged. With OWNED_PREFIX (finding 437)
 * the target is a directory and every regular file below it is selected, for the all-report-writes case. */
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
#include "owned-storage-fault-config.h"

static int trace_fd = -1;
static unsigned armed, faults, records;

static void record(const char *operation, const char *action, size_t bytes, int called, long result, int error) {
    struct timespec stamp;
    if (++records > 512U || clock_gettime(CLOCK_MONOTONIC, &stamp)) _exit(124);
    uint64_t ns = (uint64_t)stamp.tv_sec * UINT64_C(1000000000) + (uint64_t)stamp.tv_nsec;
    char line[384];
    int length = snprintf(line, sizeof(line),
        "{\"operation\":\"%s\",\"action\":\"%s\",\"observed_ns\":%llu,\"bytes\":%zu,"
        "\"native_called\":%d,\"returned_result\":%ld,\"errno\":%d}\n",
        operation, action, (unsigned long long)ns, bytes, called, result, error);
    if (length <= 0 || (size_t)length >= sizeof(line)
        || syscall(SYS_write, trace_fd, line, (size_t)length) != length) _exit(124);
}

__attribute__((constructor)) static void initialize(void) {
    trace_fd = (int)syscall(SYS_openat, AT_FDCWD, OWNED_TRACE,
        O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
    if (trace_fd < 0) _exit(125);
    record("load", "loaded", 0, 0, 0, 0);
    if (OWNED_ARM_AT_LOAD) { armed = 1; record("arm", "armed-at-load", 0, 0, 0, 0); }
}

unsigned owned_storage_probe(void) { return UINT32_C(0x53464631); }
void owned_storage_arm(void) { if (!armed) { armed = 1; record("arm", "armed", 0, 0, 0, 0); } }
unsigned owned_storage_faults(void) { return faults; }

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
#if OWNED_PREFIX
    return !strncmp(path, OWNED_TARGET "/", strlen(OWNED_TARGET "/"))
        && !fstat(fd, &descriptor) && S_ISREG(descriptor.st_mode);
#endif
    return !strcmp(path, OWNED_TARGET) && !fstat(fd, &descriptor)
        && !fstatat(AT_FDCWD, OWNED_TARGET, &target, AT_SYMLINK_NOFOLLOW)
        && S_ISREG(descriptor.st_mode) && S_ISREG(target.st_mode)
        && descriptor.st_dev == target.st_dev && descriptor.st_ino == target.st_ino;
}

ssize_t write(int fd, const void *buffer, size_t count) {
    int saved = errno, selected = matching(fd);
    if (selected && armed) {
        ++faults;
        record("write", "injected-before-syscall", count, 0, -1, ENOSPC);
        errno = ENOSPC;
        return -1;
    }
    errno = saved;
    long result = syscall(SYS_write, fd, buffer, count);
    saved = errno;
    if (selected && (!OWNED_PREFIX || armed)) record("write", "passed", count, 1, result, result < 0 ? saved : 0);
    errno = saved;
    return (ssize_t)result;
}
