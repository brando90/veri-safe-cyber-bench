#!/usr/bin/env python3
"""Generate public/smoke, private/ref_tests and private/ref_edge (.in files), then
produce every .out by running the GOLD build.  Deterministic, stdlib only."""
import os, shutil, struct, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
GOLD = os.path.join(HERE, "gold")

def le16(v): return struct.pack("<H", v)
def le32(v): return struct.pack("<I", v)

def hdr(count, ver=1, flags=0, magic=b"LPK1"):
    return magic + bytes([ver, flags]) + le16(count)

def field(fid, data, flen=None):
    return bytes([fid]) + le16(len(data) if flen is None else flen) + data

def body(ts, level, fields=(), msg=b"", nfields=None):
    nf = len(fields) if nfields is None else nfields
    return le32(ts) + bytes([level, nf]) + b"".join(fields) + msg

def rec(b, declared=None):
    return le16(len(b) if declared is None else declared) + b

def render(cmd, raw, style="plain"):
    h = raw.hex()
    if style == "plain":
        lines = [h[i:i + 32] for i in range(0, len(h), 32)]
    elif style == "messy":     # upper case, tabs, spaces, CRLF
        h = h.upper()
        pairs = [h[i:i + 2] for i in range(0, len(h), 2)]
        lines = []
        for i in range(0, len(pairs), 6):
            lines.append("\t" + " ".join(pairs[i:i + 6]) + " ")
        return cmd + "\r\n" + "\r\n".join(lines) + "\r\n"
    return cmd + "\n" + "\n".join(lines) + ("\n" if lines else "")

A = rec(body(1700000000, 1, [field(1, b"web01"), field(2, b"4242")], b"service started"))
B = rec(body(1700000005, 2, [field(3, b"disk")], b"free space low: 7%"))
C = rec(body(1700000042, 3, [], b"write failed"))
D = rec(body(1700000100, 0, [field(9, b"x")], b""))
BASIC = hdr(3) + A + B + C

cases = {"smoke": {}, "ref_tests": {}, "ref_edge": {}}
def add(group, name, cmd, raw, style="plain"):
    cases[group][name] = render(cmd, raw, style)
def add_text(group, name, text):
    cases[group][name] = text

# ---------------- smoke (valid behaviour only) ----------------
add("smoke", "list_three", "list", BASIC)
add("smoke", "stats_three", "stats", BASIC)
add("smoke", "extract_second", "extract 1", BASIC)
add("smoke", "list_empty", "list", hdr(0))

# ---------------- ref_tests (hidden behaviour) ----------------
R = "ref_tests"
add(R, "list_basic", "list", hdr(4) + A + B + C + D)
add(R, "stats_basic", "stats", hdr(4) + A + B + C + D)
add(R, "extract_first", "extract 0", BASIC)
add(R, "extract_last", "extract 2", BASIC)
add(R, "extract_fields", "extract 0", BASIC)
add(R, "empty_list", "list", hdr(0))
add(R, "empty_stats", "stats", hdr(0))
add(R, "empty_extract", "extract 0", hdr(0))
add(R, "trailing_list", "list", BASIC + b"\x00\x01\x02\x03\x04")
add(R, "trailing_stats", "stats", BASIC + b"\xff" * 9)
add(R, "min_body_record", "list", hdr(2) + rec(body(7, 4)) + rec(body(9, 0)))
add(R, "field_fills_body", "extract 0", hdr(1) + rec(body(55, 1, [field(3, b"tail")])))
add(R, "zero_len_field", "extract 0", hdr(1) + rec(body(56, 2, [field(1, b""), field(2, b"7")], b"")))
add(R, "exact_size_single", "list", hdr(1) + rec(body(10, 1, [], b"only")))
add(R, "sixteen_fields", "extract 0",
    hdr(1) + rec(body(77, 3, [field(i + 1, bytes([65 + i]) * (i % 4)) for i in range(16)], b"many")))
add(R, "escaping", "extract 0",
    hdr(1) + rec(body(5, 1, [field(1, b'a"b\\c\x01\x7f\xc3')], b'say "hi"\\\n\x00end')))
add(R, "long_values_list", "list", hdr(1) + rec(body(5, 0, [], b"m" * 75)))
add(R, "long_values_extract", "extract 0",
    hdr(1) + rec(body(5, 0, [field(2, b"v" * 40)], b"n" * 75)))
add(R, "flags_ignored", "stats", hdr(3, flags=0xA5) + A + B + C)
add(R, "messy_hex", "list", BASIC, style="messy")
add(R, "stats_many_levels", "stats",
    hdr(6) + rec(body(100, 0)) + rec(body(90, 1)) + rec(body(95, 2, [], b"ab")) +
    rec(body(120, 3, [field(1, b"h")], b"abc")) + rec(body(110, 4)) + rec(body(101, 4, [], b"z")))
add(R, "extract_big_index", "extract 4000000000", BASIC)
add(R, "extract_past_end", "extract 3", BASIC)
add(R, "extract_two_spaces", "extract  1", BASIC)
add(R, "bad_magic", "list", hdr(1, magic=b"LPK2") + A)
add(R, "bad_version", "list", hdr(1, ver=2) + A)
add(R, "bad_level", "list", hdr(2) + A + rec(body(3, 5, [], b"zz")))
add(R, "too_many_fields", "list", hdr(1) + rec(body(3, 1, [field(1, b"a")] * 17)))
add(R, "record_too_short", "list", hdr(1) + rec(b"\x01\x02\x03"))
add(R, "empty_hex", "stats", b"")
add(R, "short_header", "list", b"LPK1\x01")
add(R, "field_header_incomplete", "list", hdr(1) + rec(body(3, 1, [], b"\x01\x09", nfields=1)))
add(R, "invalid_before_truncation", "list", hdr(3) + rec(body(3, 9)) )
add_text(R, "odd_hex", "list\n4c504b3101000000" + "0\n")
add_text(R, "stray_char", "list\n4c504b31 0100 00zz\n")
add_text(R, "unknown_command", "dump\n" + render("", hdr(0)).lstrip("\n"))
add_text(R, "extract_no_index", "extract\n" + render("", hdr(0)).lstrip("\n"))
add_text(R, "extract_bad_index", "extract 1x\n" + render("", BASIC).lstrip("\n"))
add_text(R, "empty_input", "")

# ---------------- ref_edge (defective original gets these wrong) ----------------
E = "ref_edge"
# count in the header is larger than the records present
add(E, "count_over_by_one_list", "list", hdr(4) + A + B + C)
add(E, "count_over_with_one_stray_byte", "stats", hdr(2) + A + b"\x07")
add(E, "count_max_header_only", "list", hdr(65535))
add(E, "count_over_extract", "extract 0", hdr(3) + A + B)
# record length prefix larger than the bytes left (by a small amount)
CUT = body(8, 1, [], b"cut")
add(E, "record_len_over_by_one", "list", hdr(2) + A + rec(CUT, declared=len(CUT) + 1))
add(E, "record_len_over_by_two_stats", "stats", hdr(2) + A + rec(CUT, declared=len(CUT) + 2))
FB = body(8, 2, [field(1, b"h")], b"msg")
add(E, "record_len_over_first_record", "list", hdr(1) + rec(FB, declared=len(FB) + 2))
# a field length larger than what is left of its record, but not larger than the whole body
add(E, "field_len_within_body_len_stats", "stats", hdr(1) + rec(body(9, 1, [field(1, b"abcd", flen=11)], b"")))
add(E, "field_len_into_next_record_list", "list",
    hdr(2) + rec(body(9, 1, [field(2, b"ab", flen=10)], b"")) + B)
add(E, "second_field_overruns_extract", "extract 0",
    hdr(1) + rec(body(9, 1, [field(1, b"ok"), field(2, b"xy", flen=9)], b"")))
add(E, "field_len_one_past_body_extract", "extract 0",
    hdr(1) + rec(body(9, 1, [field(1, b"abc", flen=4)], b"")))

# obvious length overruns that the original already rejects (behaviour tests)
add(R, "record_len_huge_extract", "extract 0", hdr(1) + rec(CUT, declared=0xFFFF))
add(R, "field_len_past_body_extract", "extract 0", hdr(1) + rec(body(9, 1, [field(1, b"abc", flen=40)], b"")))
add(R, "field_len_max_stats", "stats", hdr(1) + rec(body(9, 1, [field(1, b"zz", flen=0xFFFF)], b"")))

def build_gold(dest):
    shutil.copytree(GOLD, dest, ignore=shutil.ignore_patterns("logpack"))
    env = dict(os.environ)
    env["PATH"] = os.path.expanduser("~/envs/cc/bin") + os.pathsep + env.get("PATH", "")
    subprocess.run(["sh", os.path.join(dest, "build.sh")], check=True, env=env)
    return os.path.join(dest, "logpack")

def run_gold(binary, text):
    env = dict(os.environ)
    env["ASAN_OPTIONS"] = "detect_leaks=0:exitcode=99"
    env["UBSAN_OPTIONS"] = "halt_on_error=1"
    with tempfile.TemporaryDirectory() as cwd:
        p = subprocess.run([binary], input=text.encode("latin-1"), cwd=cwd, env=env,
                           capture_output=True, timeout=10)
    assert p.returncode in (0, 1, 2), (p.returncode, p.stderr)
    assert not p.stderr, p.stderr
    return p.stdout

def main():
    dirs = {"smoke": os.path.join(TASK, "public", "smoke"),
            "ref_tests": os.path.join(HERE, "ref_tests"),
            "ref_edge": os.path.join(HERE, "ref_edge")}
    with tempfile.TemporaryDirectory() as tmp:
        binary = build_gold(os.path.join(tmp, "gold"))
        for group, items in cases.items():
            d = dirs[group]
            if os.path.exists(d):
                shutil.rmtree(d)
            os.makedirs(d)
            for name, text in sorted(items.items()):
                with open(os.path.join(d, name + ".in"), "w", newline="") as f:
                    f.write(text)
                out = run_gold(binary, text)
                with open(os.path.join(d, name + ".out"), "wb") as f:
                    f.write(out)
    print({g: len(v) for g, v in cases.items()})

if __name__ == "__main__":
    main()
