# VSC-HX-14 eventlane: root causes and fixes

Every fix is in `out/patch/`. Each one was confirmed by a test in `out/tests/`
that fails on the original build (it exits 86 with `INVARIANT:`, prints wrong
output or crashes) and passes on the patched build. The patched build still
passes all `smoke/` examples.

| # | File | Root cause | Fix | Test |
|---|------|-----------|-----|------|
| 1 | civil.py | `civil_from_days` was missing the `- doe // 146096` term. The last day of each 400-year era (Feb 29 of 1600, 2000, 2400, ...) converted to the wrong date, breaking property 1. | Restored the term. | t01 |
| 2 | offsets.py | `fmt` took the sign from the truncated hour count. Offsets between -59 and -1 minutes (for example `-00:30`) were written `+00:30`, breaking property 2. | Take the sign from the minutes. | t02 |
| 3 | timeparse.py | `snap` carried a rounded-up minute into the hour but not into the day, month or year. `23:59:30` became `00:00` of the same day, so the start moved by about 24 hours (property 5). | Round the raw second count to the nearest minute (half up) so the carry reaches the day, month and year. The range check is still applied to the result. | t03 |
| 4 | ids.py | The reference width came from `int(math.log(n, 32)) + 1`, and floating-point rounding gave 11 digits with a leading zero for the largest numbers (2^50-2, 2^50-1). Property 9 broke and such references could not be read back. | Width is now `(n.bit_length() + 4) // 5`, which is exact integer math. | t04 |
| 5 | names.py | `natural_key` only used the first two chunks of an id, so ids such as `room1b2` and `room1b10` tied and kept insertion order. This broke the agenda tie order (property 10). | Use every chunk. | t05 |
| 6 | fields.py | `normalize_title` replaced `"  "` with `" "` in a single pass, so runs of three or more blanks left a double space (property 4). | Use one `re.sub(r"[ \t]+", " ")` after stripping the ends. | t06 |
| 7 | fields.py | `esc_item` escaped commas but not backslashes, so a category containing `\` did not survive `join_list`/`split_list` (property 3, and README: "a comma or backslash ... is written with a backslash in front of it"). | Escape the backslash first, then the comma. | t07 |
| 8 | varint.py | `put` looped `while n > 0x80`, so any value whose remaining part was exactly 128 was written as a single byte with the continuation bit set. Packed records could then not be decoded (property 6). This hit ordinary data such as dur 128 s, seq 128, 02:08 local time and day 64. | Loop `while n >= 0x80`. | t08 |
| 9 | expand.py | The weekly generator counted weeks from the start date itself, not from the Monday of the start's week. With `every>1` and several weekdays, dates fell outside the selected weeks (property 7). | `ws = civil.week_start(start)`. | t09 |
| 10 | events.py | `reschedule` removed stale skips before it set the new start, so `event move` kept skips against the old series. Those skips then no longer named occurrences (property 8). | Set start/raw first, then drop stale skips. | t10 |

Hardening (no change to accepted ordinary input):

* exporter.py `check_imported`: a packed record could carry a UTC offset outside -12:00..+14:00 or a start day outside years 1..9999. Such an event was stored and then failed the self-check after every later command. Both are now refused as `bad record`, the same as other rule-breaking records (t11).
* Numeric checks used `str.isdigit()` before `int()`. Characters such as `²` pass `isdigit` but make `int()` raise, which crashed the program with a traceback. They now use `str.isdecimal()`, which is exactly the set `int()` accepts, so these inputs get the usual `error:` message (t12).
