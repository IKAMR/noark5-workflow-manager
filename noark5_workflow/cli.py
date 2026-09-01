from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.run_overview_log import RunOverviewLog
from noark5_workflow.app import build_registry
from noark5_workflow.core.batch_runner import BatchRunner
from noark5_workflow.core.job import Job
from noark5_workflow.core.job_runner import JobRunner
from noark5_workflow.core.job_store import JobListFormatError, load_job_list, save_job_list
from noark5_workflow.core.preflight import JobPreflight
from noark5_workflow.executors.local import LocalExecutor
from settings import load_config
from version import APP_NAME, VERSION

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_PREFLIGHT = 3
EXIT_RUN_FAILED = 4
EXIT_WAITING = 5
EXIT_NOT_FOUND = 6


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="n5wf", description=f"{APP_NAME} CLI")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    objects = parser.add_subparsers(dest="object", required=True)

    jobs = objects.add_parser("jobs", help="Work with .n5jobs job lists")
    actions = jobs.add_subparsers(dest="action", required=True)

    check = actions.add_parser("check", help="Check a job list without running it")
    check.add_argument("joblist", type=Path)

    status = actions.add_parser("status", help="Show job-list or single-job status")
    status.add_argument("joblist", type=Path)
    status.add_argument(
        "--job",
        dest="job_id",
        metavar="JOB-ID",
        help="Show detailed status for one job in the job list",
    )

    run = actions.add_parser("run", help="Run a job list without the GUI")
    run.add_argument("joblist", type=Path)
    run.add_argument(
        "--rerun",
        action="store_true",
        help="Allow jobs that have already reached a terminal state to run again",
    )
    return parser


def _load(path: Path):
    if not path.is_file():
        raise JobListFormatError(f"Jobblisten finnes ikke: {path}")
    return load_job_list(path)


def _print_report(report) -> None:
    for change in report.changes:
        print(f"NORMALIZED {change.job_id}: {change.code}")
    for conflict in report.output_conflicts:
        print(
            f"ERROR output conflict: {conflict.first_job_id} and "
            f"{conflict.second_job_id} -> {conflict.output_root}"
        )
    if report.rerun_jobs:
        print("RERUN required: " + ", ".join(job.job_id for job in report.rerun_jobs))


def _progress_percent(job: Job) -> str:
    return f"{max(0.0, min(1.0, float(job.progress))) * 100:.0f}%"


def _status_summary(path: Path, loaded) -> int:
    jobs = loaded.batch.jobs()
    print(f"{APP_NAME} {VERSION}")
    print(f"Job list: {path}")
    print(f"Jobs: {len(jobs)}")
    if loaded.active_job_id:
        print(f"Active job: {loaded.active_job_id}")
    if loaded.modified_at:
        print(f"Modified: {loaded.modified_at}")
    print()

    if not jobs:
        print("Jobblisten er tom.")
        return EXIT_OK

    id_width = max(len("Job ID"), *(len(job.job_id) for job in jobs))
    status_width = max(len("Status"), *(len(job.status.value) for job in jobs))
    progress_width = len("Progress")
    print(f"{'Job ID':<{id_width}}  {'Status':<{status_width}}  {'Progress':>{progress_width}}  Name")
    print(f"{'-' * id_width}  {'-' * status_width}  {'-' * progress_width}  {'-' * 4}")
    for job in jobs:
        print(
            f"{job.job_id:<{id_width}}  {job.status.value:<{status_width}}  "
            f"{_progress_percent(job):>{progress_width}}  {job.name}"
        )
    return EXIT_OK


def _status_job(path: Path, loaded, job_id: str) -> int:
    job = loaded.batch.get(job_id)
    if job is None:
        print(f"ERROR: Jobb-ID finnes ikke i jobblisten: {job_id}", file=sys.stderr)
        return EXIT_NOT_FOUND

    total = len(job.workflow_ids)
    next_index = max(0, min(int(job.next_operation_index), total))
    next_operation = job.workflow_ids[next_index] if next_index < total else "-"

    print(f"{APP_NAME} {VERSION}")
    print(f"Job list: {path}")
    print(f"Job ID: {job.job_id}")
    print(f"Name: {job.name}")
    print(f"Status: {job.status.value}")
    print(f"Progress: {_progress_percent(job)}")
    print(f"Source: {job.source_root}")
    print(f"Output: {job.output_root if job.output_root is not None else '-'}")
    print(f"Worker: {job.worker or '-'}")
    print(f"Workflow operations: {total}")
    print(f"Next operation index: {next_index}")
    print(f"Next operation: {next_operation}")
    print("Checkpoints: " + (", ".join(job.checkpoint_after) if job.checkpoint_after else "-"))
    print(f"Message: {job.message or '-'}")
    return EXIT_OK


def _status(path: Path, *, job_id: str | None = None) -> int:
    # Status is deliberately read-only: no preflight normalization and no save.
    loaded = _load(path)
    if job_id:
        return _status_job(path, loaded, job_id)
    return _status_summary(path, loaded)


def _check(path: Path) -> int:
    loaded = _load(path)
    jobs = loaded.batch.jobs()
    report = JobPreflight().check(jobs)
    print(f"{APP_NAME} {VERSION}")
    print(f"Job list: {path}")
    print(f"Jobs: {len(jobs)}")
    _print_report(report)
    if not report.ok:
        print("Preflight: FAILED")
        return EXIT_PREFLIGHT
    print("Preflight: OK")
    return EXIT_OK


def _run(path: Path, *, allow_rerun: bool) -> int:
    loaded = _load(path)
    jobs = loaded.batch.jobs()
    preflight = JobPreflight()
    report = preflight.check(jobs)

    print(f"{APP_NAME} {VERSION}")
    print(f"Job list: {path}")
    print(f"Jobs: {len(jobs)}")
    _print_report(report)

    if not report.ok:
        print("Run blocked by preflight errors.")
        return EXIT_PREFLIGHT
    if report.rerun_required and not allow_rerun:
        print("Run blocked: use --rerun to approve rerunning completed/failed/skipped jobs.")
        return EXIT_PREFLIGHT

    settings = load_config()
    runner = JobRunner(build_registry(), LocalExecutor(), settings)
    batch_runner = BatchRunner(runner)
    overview = RunOverviewLog(
        settings,
        run_type="batch",
        app_version=VERSION,
        job_list_path=path,
        planned_jobs=len(jobs),
    )
    overview.set_phase("CLI batch started")

    def log(job: Job, message: str) -> None:
        print(f"{job.job_id}: {message}")

    def preparing(job: Job, position: int, total: int) -> None:
        print(f"[{position}/{total}] {job.job_id} preparing")

    def registered(job: Job, position: int, total: int, will_run: bool) -> None:
        overview.start_job(job)

    def finished(job: Job, position: int, total: int) -> None:
        overview.finish_job(job)
        save_job_list(
            path,
            loaded.batch,
            active_job_id=loaded.active_job_id,
            app_version=VERSION,
        )
        print(f"[{position}/{total}] {job.job_id} -> {job.status.value}")

    try:
        outcome = batch_runner.run(
            jobs,
            log_cb=log,
            preparing_cb=preparing,
            registered_cb=registered,
            finished_cb=finished,
        )
        status = "FEIL" if outcome.failed else ("VENTER" if outcome.waiting else "FERDIG")
        overview.finish(status)
        save_job_list(
            path,
            loaded.batch,
            active_job_id=loaded.active_job_id,
            app_version=VERSION,
        )
    except Exception as exc:
        overview.fail(exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_RUN_FAILED

    print(
        f"Done: total={outcome.total}, ok={outcome.finished}, waiting={outcome.waiting}, "
        f"failed={outcome.failed}, skipped={outcome.skipped}"
    )
    print(f"Run log: {overview.path}")
    if outcome.failed:
        return EXIT_RUN_FAILED
    if outcome.waiting:
        return EXIT_WAITING
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.object == "jobs" and args.action == "check":
            return _check(args.joblist)
        if args.object == "jobs" and args.action == "status":
            return _status(args.joblist, job_id=args.job_id)
        if args.object == "jobs" and args.action == "run":
            return _run(args.joblist, allow_rerun=args.rerun)
    except JobListFormatError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_PREFLIGHT
    parser.error("Unsupported command")
    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
