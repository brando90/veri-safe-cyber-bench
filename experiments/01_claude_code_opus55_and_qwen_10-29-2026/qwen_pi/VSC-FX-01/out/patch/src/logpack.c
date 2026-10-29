#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define MAGIC 0xdeadbeef

typedef struct {
    uint32_t length;
    uint8_t *payload;
} Record;

int main() {
    uint8_t buffer[4096];
    size_t buffer_len = 0;

    // Read input as hex
    while (scanf("%2hhx", &buffer[buffer_len++]) == 1) {
        if (buffer_len == sizeof(buffer)) {
            fprintf(stderr, "error: input too large\n");
            return 1;
        }
    }

    // Validate archive
    if (buffer_len < 4) {
        fprintf(stderr, "error: truncated archive\n");
        return 2;
    }

    uint32_t magic = *(uint32_t*)buffer;
    if (magic != MAGIC) {
        fprintf(stderr, "error: invalid magic\n");
        return 1;
    }

    size_t offset = 4;
    while (offset + 4 <= buffer_len) {
        uint32_t length = *(uint32_t*)(buffer + offset);
        offset += 4;

        if ((buffer_len - offset) < length) {
            fprintf(stderr, "error: truncated archive\n");
            return 2;
        }

        // Process payload (currently just validation)
        offset += length;
    }

    if (offset != buffer_len) {
        fprintf(stderr, "error: trailing bytes\n");
        return 1;
    }

    return 0;
}