#include <stdlib.h>
#include <string.h>
#include "logpack.h"

static unsigned rd16(const uint8_t *p)
{
    return (unsigned)p[0] | ((unsigned)p[1] << 8);
}

static uint32_t rd32(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

const char *lp_status_message(lp_status st)
{
    switch (st) {
    case LP_OK:          return "ok";
    case LP_E_TRUNCATED: return "truncated archive";
    case LP_E_MAGIC:     return "bad magic";
    case LP_E_VERSION:   return "unsupported version";
    case LP_E_RECORD:    return "invalid record";
    }
    return "unknown error";
}

lp_status lp_record_parse(const uint8_t *body, size_t body_len, lp_record *out)
{
    size_t pos;
    unsigned i, nfields;

    memset(out, 0, sizeof *out);
    out->body_len = body_len;
    if (body_len < LP_MIN_BODY)
        return LP_E_RECORD;
    out->ts = rd32(body);
    out->level = body[4];
    nfields = body[5];
    if (out->level > LP_MAX_LEVEL)
        return LP_E_RECORD;
    if (nfields > LP_MAX_FIELDS)
        return LP_E_RECORD;
    out->nfields = nfields;

    pos = LP_MIN_BODY;
    for (i = 0; i < nfields; i++) {
        size_t flen;

        /* the 3-byte field header must fit in the rest of the body */
        if (body_len - pos < 3)
            return LP_E_TRUNCATED;
        flen = rd16(body + pos + 1);
        if (pos + 3 + flen > body_len)
            return LP_E_TRUNCATED;
        out->fields[i].id = body[pos];
        out->fields[i].len = flen;
        out->fields[i].data = body + pos + 3;
        pos += 3 + flen;
    }
    /* whatever is left of the body is the message text */
    if (pos > body_len)
        return LP_E_TRUNCATED;
    out->msg = body + pos;
    out->msg_len = body_len - pos;
    return LP_OK;
}

lp_status lp_archive_open(lp_archive *a, const uint8_t *buf, size_t size)
{
    size_t pos;
    unsigned i, count;

    memset(a, 0, sizeof *a);
    if (size < 8)
        return LP_E_TRUNCATED;
    if (memcmp(buf, "LPK1", 4) != 0)
        return LP_E_MAGIC;
    if (buf[4] != 1)
        return LP_E_VERSION;
    /* buf[5] is the flags byte, reserved and ignored */
    count = ((unsigned)buf[6]) | ((unsigned)buf[7] << 8);

    a->buf = buf;
    a->size = size;
    a->count = count;
    a->index = calloc(count ? count : 1, sizeof *a->index);
    if (a->index == NULL)
        return LP_E_RECORD;

    pos = 8;
    for (i = 0; i < count; i++) {
        size_t body_len, body_off;
        lp_record rec;
        lp_status st;

        body_len = ((unsigned)buf[pos]) | ((unsigned)buf[pos+1] << 8);
        body_off = pos + 2;
        if (body_off + body_len > size) {
            free(a->index);
            a->index = NULL;
            return LP_E_TRUNCATED;
        }
        st = lp_record_parse(buf + body_off, body_len, &rec);
        if (st != LP_OK) {
            free(a->index);
            a->index = NULL;
            return st;
        }
        a->index[i].body_off = body_off;
        a->index[i].body_len = body_len;
        pos = body_off + body_len;
    }
    /* bytes after the last record are ignored */
    a->end = pos;
    return LP_OK;
}

lp_status lp_archive_get(const lp_archive *a, unsigned i, lp_record *out)
{
    if (i >= a->count)
        return LP_E_RECORD;
    return lp_record_parse(a->buf + a->index[i].body_off,
                           a->index[i].body_len, out);
}

void lp_archive_close(lp_archive *a)
{
    free(a->index);
    a->index = NULL;
    a->count = 0;
}