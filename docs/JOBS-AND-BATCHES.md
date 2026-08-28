# Jobs and batches

Introduced in v0.1.1-a1.

## User-facing hierarchy

The GUI should remain simple even when execution grows beyond one extraction:

1. **Jobs** – overview of one or more jobs.
2. **Workflow** – detailed workspace for one selected job.
3. **Results** – later aggregate results for a batch.

Scheduler and Worker are technical layers and should normally appear only as status information.

## Core model

```text
Batch
├── Job 001 -> source A -> workflow -> output A
├── Job 002 -> source B -> workflow -> output B
└── Job 003 -> source C -> workflow -> output C
```

A **Job** is one source/extraction plus one workflow execution and one output context.

A **JobBatch** is an ordered collection of jobs. In a1 it is in-memory and local. It is intentionally the future boundary for recursive discovery and scheduling.

## Planned execution layers

```text
Workflow -> Job -> Batch -> Scheduler -> Worker
```

- Workflow: ordered operations for one job.
- Job: one source and one workflow execution.
- Batch: several jobs.
- Scheduler: queue, priority, retry and resource control.
- Worker: local or remote execution node.

v0.1.1-a1 implements Job and JobBatch only. Existing workflow execution remains local through LocalExecutor.

## Design rules

- Do not turn recursive scanning into direct GUI loops.
- Recursive discovery should create/prequalify Jobs and submit them to a Batch.
- A large job must not be copied, unpacked or hashed merely because it was discovered.
- Original/received sources remain read-only in principle.
- Each job must have isolated output/provenance when multi-job execution is implemented.
- Remote/server execution must exchange job specifications and storage references rather than forcing large payloads through the GUI.

## Active job ownership

From v0.1.1-a1.4 the main workspace always identifies the active job in the header.
Everything shown in the source, workflow, operation and log workspace belongs to that active job.

A newly created job starts with an empty workflow. Operations from the previously active job are not inherited implicitly. A future "copy workflow" or profile/batch function must be an explicit user action.
