#ifndef LOGPACK_H
#define LOGPACK_H

#include <stdint.h>
#include <stddef.h>

#define LP_MAGIC "LPK1"
#define LP_MAGIC_LEN 4
#define LP_VERSION 1
#define LP_MIN_BODY 6
#define LP_MAX_LEVEL 4
#define LP_MAX_FIELDS 16
#define LP_FIELD_HDR 3

typedef enum {
    LP_OK = 0,
    LP_E_TRUNCATED = 1,
    LP_E_MAGIC = 2,
    LP_E_VERSION = 3,
    LP_E_RECORD = 4
} lp_status;

typedef struct {
    size_t body_len;
    uint32_t ts;
    unsigned level;
    unsigned nfields;
    struct {
        unsigned id;
        size_t len;
        const uint8_t *data;
    } fields[16];
    const uint8_t *msg;
    size_t msg_len;
} lp_record;

typedef struct {
    const uint8_t *buf;
    size_t size;
    unsigned count;
    struct {
        size_t body_off;
        size_t body_len;
    } *index;
    size_t end;
} lp_archive;

const char *lp_status_message(lp_status st);
lp_status lp_archive_open(lp_archive *a, const uint8_t *buf, size_t size);
lp_status lp_archive_get(const lp_archive *a, unsigned i, lp_record *out);
void lp_archive_close(lp_archive *a);

#endif /* LOGPACK_H */