# v0.1.1-a1

First development step toward multi-extraction workflows.

## Added

- `Job` and `JobStatus` core model.
- `JobBatch` ordered collection.
- First Jobs/Batch overview GUI.
- Jobs can be created from a Noark 5 source folder and opened into the existing workflow workspace.
- Scheduler/Worker are shown as future technical layers, but execution remains local and single-job in a1.
- Automated tests for the job/batch core model.
- `docs/JOBS-AND-BATCHES.md` documents the planned hierarchy.

## Deliberately not in a1

- parallel execution
- scheduler queue
- remote workers/server
- persistent batch/project files
- recursive discovery/prequalification
- aggregate result dashboard

These are later steps built on the Job/Batch boundary rather than changes to the existing Workflow semantics.
