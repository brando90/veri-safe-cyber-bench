#!/usr/bin/env python3
"""Generates ref_tests / ref_edge / smoke files.  Expected output comes from the
gold build and is cross-checked against an independent model of the documented
behaviour (README) wherever the images are small enough for pure Python."""
import os, subprocess, sys, tempfile, re

HERE = sys.argv[1]
TASK = os.path.dirname(HERE)
LIMIT = 1 << 24
U64 = (1 << 64) - 1
SAN = re.compile(r"AddressSanitizer|runtime error:|UndefinedBehaviorSanitizer|LeakSanitizer")


def pat(n, seed):
    return ' '.join(str((i * 37 + seed * 11) % 256) for i in range(n))


# --------------------------------------------------------------- model
class Stop(Exception):
    def __init__(self, code):
        self.code = code


class Skip(Exception):
    pass


MODEL_CAP = 1 << 21


def fnv(b):
    h = 2166136261
    for x in b:
        h = ((h ^ x) * 16777619) & 0xFFFFFFFF
    return h


def model(script):
    out = []
    imgs = {}
    loading = None  # dict

    def fail(code, msg):
        out.append("error: %s\n" % msg)
        raise Stop(code)

    def num(s):
        if not s or not (s.isascii() and s.isdigit()):
            fail(1, "syntax")
        v = int(s)
        if v > U64:
            fail(1, "syntax")
        return v

    def name_ok(s):
        return 0 < len(s) < 32 and all(ch.isascii() and (ch.isalnum() or ch == '_') for ch in s)

    def need_name(s):
        if not name_ok(s):
            fail(1, "syntax")

    def lookup(n):
        if n not in imgs:
            fail(2, "unknown image")
        return imgs[n]

    def slot_check(n):
        if n not in imgs and len(imgs) >= 8:
            fail(2, "too many images")

    def checked(w, h, c):
        return w <= LIMIT and h <= LIMIT and w * h * c <= LIMIT

    def report(verb, n, im):
        if im['pix'] is None:
            raise Skip()
        out.append("%s %s %dx%dx%d fnv=%08x\n" % (verb, n, im['w'], im['h'], im['c'], fnv(im['pix'])))

    def install(n, w, h, c, pix):
        slot_check(n)
        imgs[n] = dict(w=w, h=h, c=c, tw=0, th=0, pix=pix)
        return imgs[n]

    try:
        for raw in script.split('\n')[:-1] if script.endswith('\n') else script.split('\n'):
            line = raw.split('#', 1)[0]
            p = line.lstrip(' \t')
            if loading is not None and p.startswith('rle') and (len(p) == 3 or p[3] in ' \t\r\n'):
                total = loading['w'] * loading['h'] * loading['c']
                for tk in p[3:].split():
                    if len(tk) >= 47:
                        fail(1, "syntax")
                    if '*' in tk:
                        a, b = tk.split('*', 1)
                        cnt, val = num(a), num(b)
                    else:
                        cnt, val = 1, num(tk)
                    if cnt == 0 or val > 255:
                        fail(1, "syntax")
                    if cnt > total - loading['filled']:
                        fail(2, "pixel data overflow")
                    if loading['pix'] is not None:
                        if total > MODEL_CAP:
                            loading['pix'] = None
                        else:
                            loading['pix'] += bytes([val]) * cnt
                    loading['filled'] += cnt
                continue
            tok = p.split()
            if len(tok) > 10:
                fail(1, "syntax")
            if not tok:
                continue
            if loading is not None:
                if tok[0] != 'end':
                    fail(1, "unterminated image")
                if len(tok) != 1:
                    fail(1, "syntax")
                if loading['filled'] != loading['w'] * loading['h'] * loading['c']:
                    fail(2, "pixel data length mismatch")
                im = loading
                loading = None
                report("loaded", im['name'], im)
                continue
            cmd = tok[0]
            n = len(tok)
            if cmd == 'image':
                if n not in (5, 8):
                    fail(1, "syntax")
                need_name(tok[1])
                tw = th = 0
                if n == 8:
                    if tok[5] != 'tile':
                        fail(1, "syntax")
                    tw, th = num(tok[6]), num(tok[7])
                    if tw == 0 and th == 0:
                        fail(1, "syntax")
                w, h, c = num(tok[2]), num(tok[3]), num(tok[4])
                if not (1 <= w <= LIMIT and 1 <= h <= LIMIT and 1 <= c <= 4):
                    fail(2, "bad dimensions")
                if (tw or th) and (tw < 1 or th < 1 or tw > w or th > h):
                    fail(2, "bad tile size")
                if not checked(w, h, c):
                    fail(3, "image too large")
                slot_check(tok[1])
                imgs.pop(tok[1], None)
                loading = dict(name=tok[1], w=w, h=h, c=c, tw=tw, th=th, filled=0, pix=b'')
                imgs[tok[1]] = loading
            elif cmd == 'crop':
                if n != 7:
                    fail(1, "syntax")
                need_name(tok[1])
                x, y, w, h = num(tok[3]), num(tok[4]), num(tok[5]), num(tok[6])
                s = lookup(tok[2])
                if w < 1 or h < 1 or x > s['w'] or y > s['h'] or w > s['w'] - x or h > s['h'] - y:
                    fail(2, "crop out of range")
                slot_check(tok[1])
                if s['pix'] is None:
                    raise Skip()
                rows = []
                for r in range(h):
                    o = ((y + r) * s['w'] + x) * s['c']
                    rows.append(s['pix'][o:o + w * s['c']])
                report("crop", tok[1], install(tok[1], w, h, s['c'], b''.join(rows)))
            elif cmd == 'tile':
                if n != 4:
                    fail(1, "syntax")
                need_name(tok[1])
                idx = num(tok[3])
                s = lookup(tok[2])
                if s['tw'] == 0:
                    fail(2, "no tile size")
                if s['w'] % s['tw'] or s['h'] % s['th']:
                    fail(2, "sheet not divisible by tile size")
                cols, rows_n = s['w'] // s['tw'], s['h'] // s['th']
                if idx >= cols * rows_n:
                    fail(2, "tile index out of range")
                slot_check(tok[1])
                if s['pix'] is None:
                    raise Skip()
                tx, ty = idx % cols, idx // cols
                rows = []
                for r in range(s['th']):
                    o = ((ty * s['th'] + r) * s['w'] + tx * s['tw']) * s['c']
                    rows.append(s['pix'][o:o + s['tw'] * s['c']])
                report("tile", tok[1], install(tok[1], s['tw'], s['th'], s['c'], b''.join(rows)))
            elif cmd == 'scale':
                if n != 5:
                    fail(1, "syntax")
                need_name(tok[1])
                fx, fy = num(tok[3]), num(tok[4])
                s = lookup(tok[2])
                if not (1 <= fx <= 65535 and 1 <= fy <= 65535):
                    fail(2, "bad factor")
                ow, oh = s['w'] * fx, s['h'] * fy
                if not checked(ow, oh, s['c']):
                    fail(3, "image too large")
                slot_check(tok[1])
                if s['pix'] is None or ow * oh * s['c'] > MODEL_CAP:
                    raise Skip()
                buf = bytearray()
                for oy in range(oh):
                    sy = oy // fy
                    for ox in range(ow):
                        sx = ox // fx
                        o = (sy * s['w'] + sx) * s['c']
                        buf += s['pix'][o:o + s['c']]
                report("scale", tok[1], install(tok[1], ow, oh, s['c'], bytes(buf)))
            elif cmd == 'concat':
                if n != 5:
                    fail(1, "syntax")
                need_name(tok[1])
                if tok[4] not in ('h', 'v'):
                    fail(1, "syntax")
                a, b = lookup(tok[2]), lookup(tok[3])
                if a['c'] != b['c']:
                    fail(2, "channel mismatch")
                hz = tok[4] == 'h'
                ow = a['w'] + b['w'] if hz else max(a['w'], b['w'])
                oh = max(a['h'], b['h']) if hz else a['h'] + b['h']
                if not checked(ow, oh, a['c']):
                    fail(3, "image too large")
                slot_check(tok[1])
                if a['pix'] is None or b['pix'] is None or ow * oh * a['c'] > MODEL_CAP:
                    raise Skip()
                c = a['c']
                canvas = bytearray(ow * oh * c)

                def blit(im, x0, y0):
                    for y in range(im['h']):
                        o = ((y0 + y) * ow + x0) * c
                        canvas[o:o + im['w'] * c] = im['pix'][y * im['w'] * c:(y + 1) * im['w'] * c]
                blit(a, 0, 0)
                blit(b, a['w'], 0) if hz else blit(b, 0, a['h'])
                report("concat", tok[1], install(tok[1], ow, oh, c, bytes(canvas)))
            elif cmd == 'info':
                if n != 2:
                    fail(1, "syntax")
                s = lookup(tok[1])
                if s['pix'] is None:
                    raise Skip()
                out.append("info %s %dx%dx%d bytes=%d tile=%s fnv=%08x\n" % (
                    tok[1], s['w'], s['h'], s['c'], s['w'] * s['h'] * s['c'],
                    "%dx%d" % (s['tw'], s['th']) if s['tw'] else "none", fnv(s['pix'])))
            elif cmd == 'drop':
                if n != 2:
                    fail(1, "syntax")
                lookup(tok[1])
                del imgs[tok[1]]
                out.append("dropped %s\n" % tok[1])
            else:
                fail(1, "syntax")
        if loading is not None:
            fail(1, "unterminated image")
    except Stop as e:
        return ''.join(out), e.code
    return ''.join(out), 0


# --------------------------------------------------------------- runner
def run(binary, text):
    env = dict(os.environ, ASAN_OPTIONS="detect_leaks=0:exitcode=99",
               UBSAN_OPTIONS="halt_on_error=1:exitcode=99:print_stacktrace=0")
    with tempfile.TemporaryDirectory() as d:
        try:
            r = subprocess.run([binary], input=text.encode(), capture_output=True, timeout=10, cwd=d, env=env)
        except subprocess.TimeoutExpired:
            return None, 'timeout', None
        return r.stdout.decode('latin-1'), r.stderr.decode('latin-1'), r.returncode


def expected_rc(out):
    last = out.rstrip('\n').split('\n')[-1] if out.strip() else ''
    if not last.startswith('error: '):
        return 0
    m = last[7:]
    if m in ('syntax', 'unterminated image'):
        return 1
    if m == 'image too large':
        return 3
    return 2


def passes(binary, text, want):
    o, e, rc = run(binary, text)
    if o is None or SAN.search(e):
        return False
    return o == want and rc == expected_rc(want)


# --------------------------------------------------------------- tests
T = {}   # ref_tests
E = {}   # ref_edge

T['load_rgb_mixed'] = "image px 5 2 3\nrle %s\nend\ninfo px\n" % pat(30, 1)
T['crop_window'] = "image a 6 5 2\nrle %s\nend\ncrop b a 1 1 3 2\ncrop c a 0 0 6 5\ncrop d a 5 4 1 1\ninfo b\n" % pat(60, 2)
T['tile_grid'] = ("image sh 12 8 2 tile 4 4\nrle %s\nend\ntile t0 sh 0\ntile t2 sh 2\ntile t5 sh 5\ninfo sh\ninfo t5\n" % pat(192, 3))
T['scale_nonuniform'] = "image a 3 2 3\nrle %s\nend\nscale b a 2 3\nscale c a 1 1\nscale d a 5 1\n" % pat(18, 4)
T['concat_h_pad'] = ("image a 3 2 1\nrle %s\nend\nimage b 2 4 1\nrle %s\nend\nconcat c a b h\nconcat d b a h\n" % (pat(6, 5), pat(8, 6)))
T['concat_v_pad'] = ("image a 3 2 2\nrle %s\nend\nimage b 5 1 2\nrle %s\nend\nconcat c a b v\nconcat d b a v\ninfo d\n" % (pat(12, 7), pat(10, 8)))
T['alias_dst'] = ("image a 2 3 1\nrle %s\nend\nscale a a 2 2\nconcat a a a h\nconcat a a a v\ninfo a\n" % pat(6, 9))
T['replace_and_drop'] = ("image a 2 2 1\nrle 1 2 3 4\nend\nimage a 3 1 1\nrle 7 8 9\nend\ninfo a\ndrop a\ninfo a\n")
T['too_many_images'] = ''.join("image i%d 1 1 1\nrle %d\nend\n" % (k, k) for k in range(9))
T['replace_when_full'] = (''.join("image i%d 1 1 1\nrle %d\nend\n" % (k, k) for k in range(8))
                          + "scale i3 i3 2 2\ncrop i4 i7 0 0 1 1\nconcat i5 i0 i1 h\ninfo i5\n")
T['comments_multi_rle'] = ("# header\n\n   image   a  4  2  1   # trailing comment\n  rle 1 2 # first\nrle   3*4  \n\trle 2*9 # x\nend # done\n\ninfo a\n")
T['err_channel_mismatch'] = "image a 2 2 3\nrle 12*1\nend\nimage b 2 2 1\nrle 4*1\nend\nconcat c a b h\ninfo a\n"
T['err_crop_range'] = "image a 4 4 1\nrle 16*1\nend\ncrop b a 2 2 2 2\ncrop c a 3 0 2 1\n"
T['err_crop_huge_args'] = "image a 4 4 1\nrle 16*1\nend\ncrop c a 18446744073709551615 0 2 1\n"
T['err_crop_zero'] = "image a 4 4 1\nrle 16*1\nend\ncrop c a 0 0 0 1\n"
T['err_bad_dimensions_big'] = "image a 16777217 1 1\nrle 1\nend\n"
T['err_bad_dimensions_zero'] = "image ok 1 1 1\nrle 5\nend\nimage a 4 0 1\n"
T['err_bad_channels'] = "image a 4 4 5\n"
T['err_bad_tile'] = "image a 8 8 1 tile 9 4\n"
T['err_bad_factor'] = "image a 2 2 1\nrle 4*1\nend\nscale b a 0 2\n"
T['err_bad_factor_big'] = "image a 2 2 1\nrle 4*1\nend\nscale b a 2 65536\n"
T['err_unknown_before_range'] = "image a 2 2 1\nrle 4*1\nend\nscale b nosuch 70000 70000\n"
T['err_factor_before_size'] = "image a 256 256 1\nrle 65536*1\nend\nscale b a 65536 256\n"
T['err_data_short'] = "image a 3 3 1\nrle 8*1\nend\n"
T['err_data_overflow'] = "image a 3 3 1\nrle 5*1 5*2\n"
T['err_data_value'] = "image a 2 2 1\nrle 1 2 300 4\nend\n"
T['err_syntax_command'] = "image a 1 1 1\nrle 1\nend\nrotate a 90\n"
T['err_syntax_number'] = "image a 1 1 1\nrle 1\nend\ncrop b a 0 0 -1 1\n"
T['err_unterminated_cmd'] = "image a 2 2 1\nrle 2*1\ninfo a\n"
T['err_unterminated_eof'] = "image a 2 2 1\nrle 4*1\n"
T['err_tile_none'] = "image a 4 4 1\nrle 16*1\nend\ntile t a 0\n"
T['err_tile_divisible'] = "image a 6 4 1 tile 4 4\nrle 24*1\nend\ntile t a 0\n"
T['err_tile_index'] = "image a 8 4 1 tile 4 4\nrle 32*1\nend\ntile t a 1\ntile u a 2\n"
T['boundary_load_exact'] = "image big 4096 1024 4 tile 4096 1\nrle 8388608*7 8388608*250\nend\ninfo big\ncrop c big 4000 1000 96 24\ntile t big 1023\n"
T['boundary_scale_exact'] = "image s 1024 1024 4\nrle 2097152*3 2097152*4\nend\nscale t s 2 2\ninfo t\ncrop c t 1 2 3 4\n"
T['boundary_scale_factor'] = "image p 1 1 1\nrle 77\nend\nscale q p 4096 4096\ninfo q\ncrop c q 4095 4095 1 1\n"
T['boundary_concat_exact'] = ("image a 4096 1024 2\nrle 8388608*5\nend\nimage b 4096 1024 2\nrle 8388608*6\nend\nconcat c a b h\ninfo c\n"
                              "drop c\nconcat d a b v\ninfo d\n")
T['strip_max_dim'] = "image w 16777216 1 1\nrle 16777216*9\nend\nimage t 1 16777216 1\nrle 16777216*8\nend\ncrop a w 100 0 4 1\ncrop b t 0 100 1 4\nscale s a 1 1\ninfo w\n"

E['concat_wrap_8m'] = "image w 8388608 1 1\nrle 8388608*1\nend\nimage t 1 8388608 1\nrle 8388608*2\nend\nconcat c w t h\ninfo c\n"

E['load_wrap_zero'] = "image a 65536 65536 1\nrle 4294967296*0\nend\ninfo a\n"
E['load_wrap_small'] = "image a 65537 65537 1\nrle 200000*1\nend\ninfo a\n"
E['load_wrap_channels'] = "image a 1048576 1024 4\nrle 100*1\nend\ninfo a\n"
E['load_over_limit_plain'] = "image a 4096 1025 4\nrle 16793600*5\nend\ninfo a\n"
E['load_channel_term'] = "image ok 2 2 1\nrle 4*1\nend\nimage a 4097 1024 4\nrle 16781312*5\nend\ninfo a\n"
E['load_max_dims'] = "image a 16777216 16777216 4\nrle 1*0\nend\ninfo a\n"
E['scale_wrap_zero'] = "image s 256 256 1\nrle 65536*3\nend\nscale t s 256 256\ninfo t\n"
E['scale_wrap_small'] = "image s 2 2 1\nrle 1 2 3 4\nend\nscale t s 32769 32769\ninfo t\n"
E['scale_over_limit_plain'] = "image s 2048 2048 1\nrle 4194304*9\nend\nscale t s 2 3\ninfo t\n"
E['scale_factor_product'] = "image p 1 1 1\nrle 5\nend\nscale q p 65535 257\ninfo q\n"
E['scale_exact_then_over'] = "image p 1 1 1\nrle 5\nend\nscale q p 4096 4096\nscale r q 1 2\ninfo r\n"
E['concat_h_wrap_small'] = "image a 65536 1 1\nrle 65536*1\nend\nimage b 1 65536 1\nrle 65536*2\nend\nconcat c a b h\ninfo c\n"
E['concat_v_wrap_small'] = "image a 1 65536 1\nrle 65536*1\nend\nimage b 65536 1 1\nrle 65536*2\nend\nconcat c a b v\ninfo c\n"
E['concat_wrap_zero'] = "image a 65535 1 1\nrle 65535*1\nend\nimage b 1 65536 1\nrle 65536*2\nend\nconcat c a b h\ninfo c\n"
E['concat_wrap_16m'] = "image a 16777216 1 1\nrle 16777216*1\nend\nimage b 1 16777216 1\nrle 16777216*2\nend\nconcat c a b h\ninfo c\n"
E['concat_over_limit_plain'] = "image a 4096 1024 4\nrle 16777216*1\nend\nimage b 4096 1 4\nrle 16384*2\nend\nconcat c a b v\ninfo c\n"
E['concat_exact_then_over'] = ("image a 4096 1024 2\nrle 8388608*5\nend\nimage b 4096 1024 2\nrle 8388608*6\nend\nconcat c a b h\n"
                               "image z 1 1 2\nrle 2*0\nend\nconcat d c z v\ninfo d\n")
E['mixed_stops_midway'] = ("image a 300 300 1\nrle 90000*4\nend\nscale b a 3 3\ncrop c b 0 0 10 10\n"
                           "image d 1 40000 1\nrle 40000*9\nend\nconcat e b d h\ninfo c\n")
E['concat_alias_wrap'] = "image a 65535 1 1\nrle 65535*1\nend\nimage b 1 65536 1\nrle 65536*2\nend\nconcat a a b h\ninfo a\n"

SMOKE = ['basic_load', 'sheet_tile', 'scale_concat', 'err_channels', 'boundary_ok']


def write(path, text):
    with open(path, 'w', newline='') as f:
        f.write(text)


def main():
    gold = os.path.join(HERE, 'build', 'gold', 'tilekit')
    orig = os.path.join(HERE, 'build', 'original', 'tilekit')
    muts = sorted(m for m in os.listdir(os.path.join(HERE, 'mutants')))
    mbin = {m: os.path.join(HERE, 'build', m, 'tilekit') for m in muts}
    for d in ('ref_tests', 'ref_edge'):
        for f in os.listdir(os.path.join(HERE, d)):
            os.remove(os.path.join(HERE, d, f))
    killers = {m: [] for m in muts}
    problems = []
    skipped = 0
    for kind, tests in (('ref_tests', T), ('ref_edge', E)):
        for name, text in sorted(tests.items()):
            o, e, rc = run(gold, text)
            if o is None or SAN.search(e):
                problems.append("gold unclean on %s/%s: %s" % (kind, name, e[:200]))
                continue
            if rc != expected_rc(o):
                problems.append("gold rc %s on %s/%s" % (rc, kind, name))
            try:
                mo, mrc = model(text)
                if (mo, mrc) != (o, rc):
                    problems.append("MODEL MISMATCH %s/%s\n model=%r rc=%s\n gold =%r rc=%s" % (kind, name, mo, mrc, o, rc))
            except Skip:
                skipped += 1
            if kind == 'ref_edge' and not o.rstrip('\n').endswith('error: image too large'):
                problems.append("edge %s does not end in image too large" % name)
            op = passes(orig, text, o)
            if kind == 'ref_tests' and not op:
                problems.append("original FAILS ref_test %s" % name)
            if kind == 'ref_edge' and op:
                problems.append("original passes ref_edge %s" % name)
            for m in muts:
                if not passes(mbin[m], text, o):
                    killers[m].append("%s/%s" % (kind, name))
            write(os.path.join(HERE, kind, name + '.in'), text)
            write(os.path.join(HERE, kind, name + '.out'), o)
    for m in muts:
        if not killers[m]:
            problems.append("mutant %s survives" % m)
        print("mutant %-10s killed by %2d tests: %s" % (m, len(killers[m]), ', '.join(killers[m][:6])))
    # smoke
    sd = os.path.join(TASK, 'public', 'smoke')
    for s in SMOKE:
        text = open(os.path.join(sd, s + '.in')).read()
        o, e, rc = run(gold, text)
        assert not SAN.search(e)
        if not passes(orig, text, o):
            problems.append("original fails smoke %s" % s)
        try:
            if model(text) != (o, rc):
                problems.append("model mismatch smoke %s" % s)
        except Skip:
            pass
        write(os.path.join(sd, s + '.out'), o)
    print("ref_tests=%d ref_edge=%d model-skipped=%d" % (len(T), len(E), skipped))
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print(" -", p)
        sys.exit(1)


main()
