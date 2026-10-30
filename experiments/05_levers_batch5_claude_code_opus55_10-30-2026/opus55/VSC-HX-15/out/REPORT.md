# VSC-HX-15 root causes and fix (text from the solver's reply, saved by the lead; the solver was blocked from writing report files)
Each defect is a module breaking a convention from the README "Conventions between modules" table.
1. ingest.py: skew was added; positive skew means the logger runs ahead, so it now passes -skew to calib.correct.
2. ingest.py: the raw temp was clamped while parsing, before calibration; now it parses unclamped and calib.calibrate clamps last.
3. quota.py: cap 0 refused every reading; 0 now means unlimited (admit returns True).
4. alerts.py: excursion length (seconds) was compared with hold in ms, so alerts almost never fired; the limit is now in seconds (printed text unchanged).
5. ranking.py: rank sorted by the exact float share; it now sorts by integer tenths, half up, then natural id.
6. search.py: the find query was only casefolded; it now gets clean_label (NFC, blank runs collapsed, trimmed), then casefold.
7. export.py: the label was written unescaped, so labels with a backslash changed on import; it now uses tsvfmt.esc. _ms now accepts only ASCII digits.
8. legs.py: arrivals were looked up with 0-based stop numbers; leg i+1 now uses arrival_at(i+1)..arrival_at(i+2).
