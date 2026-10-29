# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Writes the .in files for public/smoke, ref_tests and ref_edge (inputs are
the source of truth; .out files are produced from gold by build_private.sh)."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
BASE = [
    "add-item A100 fasteners 40 25 10 Hex bolt M5",
    "add-item A101 fasteners 15 40 22 Hex nut M5",
    "add-item B200 tools 3 1250 900 Claw hammer",
    "add-item B201 tools 8 399 450 Tape measure 5m",
    "add-item C300 paint 12 899 600 Matt white 1L",
]

SMOKE = {
    "s1_add_and_report": BASE + ["report", "report tools"],
    "s2_find_rename": BASE + [
        "find hex", "find  M5", "rename A100 Hex bolt M5 zinc", "find bolt",
        "find nothing-here"],
    "s3_discount_export": BASE + [
        "apply-discount 10 tools", "report tools", "export-csv"],
    "s4_errors": [
        "# comment line", "",
        "add-item A1 misc 1 100 50 Widget",
        "add-item A1 misc 2 100 50 Widget again",
        "add-item bad$sku misc 1 1 1 Thing",
        "add-item A2 misc x 1 1 Thing",
        "rename Z9 Something",
        "apply-discount 150 misc",
        "apply-discount 5 nope",
        "report nope",
        "frobnicate now",
        "find widget"],
}

REF_TESTS = {
    "t01_add_report": BASE + ["report"],
    "t02_duplicate_sku": BASE[:2] + ["add-item A100 tools 1 1 1 Other", "report"],
    "t03_bad_args": [
        "add-item A1 misc 1 100 50 Widget",
        "add-item A_2-b misc 1 100 50 Okay sku",
        "add-item A!3 misc 1 100 50 Bad sku",
        "add-item A4 misc -1 100 50 Negative qty",
        "add-item A5 misc 1 1.5 50 Fractional price",
        "add-item A6 misc 1 100 1234567890 Long cost",
        "add-item A7234567890123456 misc 1 1 1 Long sku",
        "report"],
    "t04_report_filter": BASE + ["report paint", "report fasteners", "report food"],
    "t05_find_case": BASE + ["find HEX", "find m5", "find 1l", "find hammer"],
    "t06_find_spaces_none": BASE + [
        "find   Hex nut", "find tape  measure", "find zzz"],
    "t07_rename_plain": BASE + [
        "rename B200   Steel claw hammer  ", "rename C300 Gloss", "find hammer",
        "find gloss", "find matt", "report"],
    "t08_rename_unknown": BASE[:2] + ["rename X1 Nothing", "find nothing"],
    "t09_discount_rounding": BASE + [
        "apply-discount 33 fasteners", "report fasteners",
        "apply-discount 0 tools", "report tools"],
    "t10_discount_100_and_errors": BASE + [
        "apply-discount 100 paint", "report paint", "apply-discount abc tools",
        "apply-discount 101 tools", "apply-discount 5 Tools", "report"],
    "t11_export_plain": BASE + ["export-csv"],
    "t12_export_negative_margin": BASE + [
        "apply-discount 50 tools", "export-csv"],
    "t13_names_with_symbols_plain": [
        "add-item N1 misc 1 100 40 Washer #4 (zinc) - pack of 10",
        "add-item N2 misc 2 150 90 Cable 3.5mm = 2 jacks + case @ home",
        "add-item N3 misc 3 175 60 Mixed   spacing   name",
        "find #4", "find 3.5mm", "find mixed   spacing", "export-csv"],
    "t14_unknown_and_comments": [
        "# nothing but comments", "   ", "export-csv", "report", "find x",
        "bogus", "add-item A1 misc 1 1 1 One", "   # indented comment",
        "report"],
    "t15_audit_counts_many": BASE + [
        "apply-discount 10 fasteners", "rename A101 Hex nut M5 steel",
        "apply-discount 20 tools", "apply-discount 5 paint", "rename C300 Gloss white 1L",
        "report", "export-csv"],
}

REF_EDGE = {
    "e01_add_quotes_in_name": [
        "add-item Q1 misc 5 300 120 O'Neil bracket",
        "add-item Q2 misc 2 450 200 Bolt 5\" zinc",
        "add-item Q3 misc 1 99 10 'quoted' name",
        "find neil", "find 'quoted'", "find 5\"", "report", "export-csv"],
    "e02_find_text_with_quote": BASE[:2] + [
        "add-item F1 misc 4 100 50 Pipe 3/4\" copper",
        "add-item F2 misc 4 100 50 Child's cup",
        "find 3/4\"", "find child's", "find '", "find \"", "find s cup"],
    "e03_find_percent_underscore_literal": [
        "add-item W1 misc 9 500 200 Cotton 100% soft",
        "add-item W2 misc 9 500 200 M100 bolt",
        "add-item W3 misc 9 500 200 label a_b roll",
        "add-item W4 misc 9 500 200 label axb roll",
        "add-item W5 misc 9 500 200 Rate 5% off",
        "find 100%", "find a_b", "find %", "find _", "find 5%", "find 50%",
        "find %%"],
    "e04_find_semicolon_comma": [
        "add-item S1 misc 1 100 50 Nut; M5, steel",
        "add-item S2 misc 1 100 50 Nut M5 steel",
        "add-item S3 misc 1 100 50 Screw, wood; 4x40",
        "find ; M5,", "find nut m5", "find ,", "find ;", "find wood; 4x"],
    "e05_rename_to_quotes": BASE + [
        "rename A100 Bolt 5\" (zinc), O'Neil spec",
        "rename B200 It's a 'hammer'",
        "find o'neil", "find 'hammer'", "find 5\"", "report", "export-csv"],
    "e06_rename_semicolon": BASE + [
        "rename A101 Nut; M5; steel",
        "rename C300 White; 1L",
        "find nut;", "find white;", "find matt", "report"],
    "e07_rename_then_more_commands": BASE + [
        "rename A100 100% 'real' bolt; M5, zinc",
        "apply-discount 10 fasteners",
        "rename A101 \"Hex\" nut",
        "find 100%", "find \"hex\"", "report fasteners", "export-csv"],
    "e08_csv_commas_quotes_semicolons": [
        "add-item E1 misc 1 100 40 Washer, 5\" ; steel",
        "add-item E2 misc 2 200 90 Plain name",
        "add-item E3 misc 3 300 90 Semi;colon",
        "add-item E4 misc 4 400 90 Say \"hi\"",
        "add-item E5 misc 5 500 90 \"",
        "add-item E6 misc 6 600 90 a,b,c",
        "export-csv"],
    "e09_csv_formula_leading": [
        "add-item G1 misc 1 100 40 =total spares",
        "add-item G2 misc 1 100 40 +2 spare caps",
        "add-item G3 misc 1 100 40 -5mm washer",
        "add-item G4 misc 1 100 40 @home shelf",
        "add-item G5 misc 1 100 40 mid=dle +plus -minus @at",
        "add-item G6 misc 1 100 40 -",
        "add-item G7 misc 1 100 40       =padded",
        "export-csv"],
    "e10_csv_formula_and_quoting_combined": [
        "add-item H1 misc 1 100 40 =A,B",
        "add-item H2 misc 1 100 40 -\"x\"",
        "add-item H3 misc 1 100 40 @a;b",
        "add-item H4 misc 1 100 140 +1, then -2",
        "export-csv"],
    "e11_csv_categories_special": [
        "add-item K1 nuts,bolts 4 100 40 Plain one",
        "add-item K2 @shelf 4 100 40 Plain two",
        "add-item K3 a;b 4 100 40 Plain three",
        "add-item K4 -neg 4 100 140 Plain four",
        "add-item K5 q\"t 4 100 40 Plain five",
        "export-csv"],
    "e12_category_quote_report_discount": [
        "add-item M1 men's 3 1000 600 Gloves",
        "add-item M2 men's 2 2000 900 Boots",
        "add-item M3 kids 1 500 100 Socks",
        "report men's", "apply-discount 25 men's", "report men's", "report",
        "apply-discount 10 women's", "report women's", "export-csv"],
    "e13_everything_combined": BASE + [
        "add-item Z1 o'brien;x 2 1500 700 Crate, 12\" ; oak",
        "add-item Z2 o'brien;x 2 1500 700 =cheap crate",
        "find crate", "find 12\"", "rename Z2 Crate '; -2 slots, pine",
        "apply-discount 20 o'brien;x", "report o'brien;x", "find ; -2",
        "report", "export-csv"],
}

def write(sub, tests):
    d = ROOT.parent / sub if sub.startswith("public") else ROOT / sub
    d.mkdir(parents=True, exist_ok=True)
    for name, lines in tests.items():
        (d / (name + ".in")).write_text("\n".join(lines) + "\n")

# e04 passes on the original (guard against over-aggressive fixes), so it is a behaviour test, not an edge test
REF_TESTS["e04_find_semicolon_comma"] = REF_EDGE.pop("e04_find_semicolon_comma")

write("public/smoke", SMOKE)
write("ref_tests", REF_TESTS)
write("ref_edge", REF_EDGE)
