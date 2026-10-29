/* Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29. */
/* Whole-image operations that build a new, larger image: scale and concat. */
#include "tilekit.h"

#include <stdlib.h>
#include <string.h>

/* Nearest-neighbour integer upscale by fx horizontally and fy vertically. */
void op_scale(Store *st, const char *dst, const char *srcname,
              uint64_t fx, uint64_t fy)
{
    Image *src = store_lookup(st, srcname);
    unsigned char *buf;
    uint64_t ow, oh;
    uint64_t total_size;

    if (fx < 1 || fx > TK_MAX_FACTOR || fy < 1 || fy > TK_MAX_FACTOR)
        tk_fail(TK_EXIT_SEMANTIC, "bad factor");

    ow = src->w * fx;
    oh = src->h * fy;
    total_size = ow * oh * src->c;

    if (total_size > TK_MAX_BYTES)
        tk_fail(TK_EXIT_TOO_LARGE, "image too large");

    buf = malloc(total_size ? total_size : 1);
    if (!buf)
        tk_fail(TK_EXIT_SEMANTIC, "out of memory");
    for (uint64_t oy = 0; oy < oh; oy++) {
        uint64_t sy = oy / fy;

        for (uint64_t ox = 0; ox < ow; ox++) {
            uint64_t sx = ox / fx;

            for (uint64_t ch = 0; ch < src->c; ch++)
                buf[(oy * ow + ox) * src->c + ch] =
                    src->pix[(sy * src->w + sx) * src->c + ch];
        }
    }
    store_install(st, dst, buf, ow, oh, src->c);
    image_report("scale", store_lookup(st, dst));
}

/* Copies im into the canvas (row length ow pixels) with its corner at (x0, y0). */
static void blit(unsigned char *canvas, uint64_t ow, const Image *im,
                 uint64_t x0, uint64_t y0)
{
    uint64_t row = im->w * im->c, y;

    for (y = 0; y < im->h; y++)
        memcpy(canvas + ((y0 + y) * ow + x0) * im->c, im->pix + y * row, row);
}

/* Joins a and b side by side (horizontal) or stacked (vertical).  The shorter
 * (or narrower) image is padded with zero bytes. */
void op_concat(Store *st, const char *dst, const char *an, const char *bn,
               int horizontal)
{
    Image *a = store_lookup(st, an);
    Image *b = store_lookup(st, bn);
    unsigned char *buf;
    uint64_t ow, oh;
    uint64_t total_size;

    if (a->c != b->c)
        tk_fail(TK_EXIT_SEMANTIC, "channel mismatch");

    if (horizontal) {
        ow = a->w + b->w;
        oh = a->h > b->h ? a->h : b->h;
    } else {
        ow = a->w > b->w ? a->w : b->w;
        oh = a->h + b->h;
    }
    total_size = ow * oh * a->c;

    if (total_size > TK_MAX_BYTES)
        tk_fail(TK_EXIT_TOO_LARGE, "image too large");

    buf = malloc(total_size ? total_size : 1);
    if (!buf)
        tk_fail(TK_EXIT_SEMANTIC, "out of memory");
    memset(buf, 0, total_size);
    blit(buf, ow, a, 0, 0);
    if (horizontal)
        blit(buf, ow, b, a->w, 0);
    else
        blit(buf, ow, b, 0, a->h);
    store_install(st, dst, buf, ow, oh, a->c);
    image_report("concat", store_lookup(st, dst));
}
