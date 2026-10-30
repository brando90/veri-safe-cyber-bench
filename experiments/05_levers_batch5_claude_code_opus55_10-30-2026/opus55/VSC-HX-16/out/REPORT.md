# VSC-HX-16 root causes and fix (text from the solver's reply, saved by the lead; the solver's file tool refused .md files)
1. maskers: values shorter than 4 characters were shown in clear.
2. policy: prefix rules used only the last prefix added (late-bound loop variable).
3. policy/cmds: `export keep=` changed the policy permanently (shallow copy).
4. names: `x-` stripped as a character set instead of one prefix.
5. records: field names split at the last `=`.
6. scanner: message scrubbing ignored case and stopped after 2 pairs.
7. store: `purge` skipped a record after each removal (the exit 86 failure).
8. policy: a source limit of 0 fell back to the default.
9. reports: equal counts listed in reverse name order.
10. reports: shares rounded halves to even instead of up.
