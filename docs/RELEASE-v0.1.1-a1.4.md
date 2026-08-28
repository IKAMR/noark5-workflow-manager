# v0.1.1-a1.4

Correction of the first Job/Batch GUI prototype.

- The active job is now shown prominently in the main header.
- A new job starts with an empty workflow and does not silently inherit operations from the previous job.
- The header explicitly tells the user when the active job has zero operations.
- Retains the CustomTkinter `width=None` fix from a1.2.
- `test.bat` clears the previous machine-readable summary before running, so a failed test startup cannot display stale PASS counts.
