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

    run = actions.add_parser("run", help="Run a job list or one selected job without the GUI")
    run.add_argument("joblist", type=Path)
    run.add_argument(
        "--job",
        dest="job_id",
        metavar="JOB-ID",
        help="Run only one job from the job list",
    )
    run.add_argument(
        "--rerun",
        action="store_true",
        help="Allow jobs that have already reached a terminal state to run again",
    )

    continue_cmd = actions.add_parser(
        "continue",
        help="Continue one selected job from its current checkpoint",
    )
    continue_cmd.add_argument("joblist", type=Path)
    continue_cmd.add_argument(
        "--job",
        dest="job_id",
        metavar="JOB-ID",
        required=True,
        help="Continue one waiting job from the job list",
    )
    return parser


def _load(path: Path):
    if not path.is_file():
        raise JobListFormatError(f"Jobblisten finnes ikke: {path}")
    return load_job_list(path)


_CHANGED_AFTER_RUN = "Konfigurasjon endret - klar for ny kjøring"


def _rerun_reason(job: Job) -> str:
    if job.message == _CHANGED_AFTER_RUN:
        return "configuration_changed"
    return "previous_terminal_run"


def _display_status(job: Job) -> str:
    if job.status.value == "Klar" and job.message == _CHANGED_AFTER_RUN:
        return "Klar – endret etter kjøring"
    return job.status.value


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
    status_width = max(len("Status"), *(len(_display_status(job)) for job in jobs))
    progress_width = len("Progress")
    print(f"{'Job ID':<{id_width}}  {'Status':<{status_width}}  {'Progress':>{progress_width}}  Name")
    print(f"{'-' * id_width}  {'-' * status_width}  {'-' * progress_width}  {'-' * 4}")
    for job in jobs:
        print(
            f"{job.job_id:<{id_width}}  {_display_status(job):<{status_width}}  "
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
    print(f"Status: {_display_status(job)}")
    print(f"Progress: {_progress_percent(job)}")
    print(f"Source: {job.source_root}")
    print(f"Output: {job.output_root if job.output_root is not None else '-'}")
    print(f"Worker: {job.worker or '-'}")
    print(f"Workflow operations: {total}")
    print(f"Next operation index: {next_index}")
    print(f"Next operation: {next_operation}")
    print("Checkpoints: " + (", ".join(job.checkpoint_after) if job.checkpoint_after else "-"))
    print(f"Message: {job.message or '-'}")
    rerun_required = (
        job.status.value in {"Ferdig", "Feil", "Hoppet over"}
        or job.message == _CHANGED_AFTER_RUN
    )
    print(f"Rerun approval required: {'yes' if rerun_required else 'no'}")
    if rerun_required:
        reason = (
            "configuration changed after previous run"
            if job.message == _CHANGED_AFTER_RUN
            else "job has previous terminal run"
        )
        print(f"Rerun reason: {reason}")
    return EXIT_OK


def _status(path: Path, *, job_id: str | None = None) -> int:
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


def _selected_preflight(loaded, selected: Job):
    preflight = JobPreflight()
    report = preflight.check([selected])
    all_conflicts = preflight.check_outputs(loaded.batch.jobs())
    report.output_conflicts = [
        conflict
        for conflict in all_conflicts
        if selected.job_id in {conflict.first_job_id, conflict.second_job_id}
    ]
    return report


def _run_one(path: Path, loaded, selected: Job, *, allow_rerun: bool) -> int:
    report = _selected_preflight(loaded, selected)

    print(f"{APP_NAME} {VERSION}")
    print(f"Job list: {path}")
    print(f"Selected job: {selected.job_id}")
    _print_report(report)

    if not report.ok:
        print("Run blocked by preflight errors.")
        return EXIT_PREFLIGHT
    if report.rerun_required and not allow_rerun:
        if _rerun_reason(selected) == "configuration_changed":
            print("Run blocked: job configuration changed after a previous run.")
            print("Use --rerun to approve a new run with the updated configuration.")
        else:
            print("Run blocked: selected job has already reached a terminal state.")
            print("Use --rerun to approve running the selected job again.")
        return EXIT_PREFLIGHT

    settings = load_config()
    runner = JobRunner(build_registry(), LocalExecutor(), settings)
    overview = RunOverviewLog(
        settings,
        run_type="job",
        app_version=VERSION,
        job_list_path=path,
        planned_jobs=1,
    )
    overview.set_phase(f"CLI job started: {selected.job_id}")
    overview.start_job(selected)

    def log(message: str) -> None:
        print(f"{selected.job_id}: {message}")

    def state_changed(job: Job) -> None:
        save_job_list(
            path,
            loaded.batch,
            active_job_id=job.job_id,
            app_version=VERSION,
        )

    try:
        outcome = runner.run(
            selected,
            log_cb=log,
            state_cb=state_changed,
        )
        overview.finish_job(selected)
        status = "FEIL" if not outcome.ok else (
            "VENTER" if selected.status.value == "Venter ved kontrollpunkt" else "FERDIG"
        )
        overview.finish(status)
        save_job_list(
            path,
            loaded.batch,
            active_job_id=selected.job_id,
            app_version=VERSION,
        )
    except Exception as exc:
        overview.fail(exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_RUN_FAILED

    print(f"{selected.job_id} -> {selected.status.value}")
    print(f"Run log: {overview.path}")
    if not outcome.ok:
        return EXIT_RUN_FAILED
    if selected.status.value == "Venter ved kontrollpunkt":
        return EXIT_WAITING
    return EXIT_OK


def _continue_one(path: Path, loaded, selected: Job) -> int:
    print(f"{APP_NAME} {VERSION}")
    print(f"Job list: {path}")
    print(f"Selected job: {selected.job_id}")

    settings = load_config()
    runner = JobRunner(build_registry(), LocalExecutor(), settings)
    overview = RunOverviewLog(
        settings,
        run_type="job",
        app_version=VERSION,
        job_list_path=path,
        planned_jobs=1,
    )
    overview.set_phase(f"CLI job continue started: {selected.job_id}")
    overview.start_job(selected)

    def log(message: str) -> None:
        print(f"{selected.job_id}: {message}")

    def state_changed(job: Job) -> None:
        save_job_list(
            path,
            loaded.batch,
            active_job_id=job.job_id,
            app_version=VERSION,
        )

    try:
        outcome = runner.continue_job(
            selected,
            log_cb=log,
            state_cb=state_changed,
        )
        overview.finish_job(selected)
        status = "FEIL" if not outcome.ok else (
            "VENTER" if selected.status.value == "Venter ved kontrollpunkt" else "FERDIG"
        )
        overview.finish(status)
        save_job_list(
            path,
            loaded.batch,
            active_job_id=selected.job_id,
            app_version=VERSION,
        )
    except ValueError as exc:
        overview.fail(exc)
        print(f"Continue blocked: {exc}")
        return EXIT_PREFLIGHT
    except Exception as exc:
        overview.fail(exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_RUN_FAILED

    print(f"{selected.job_id} -> {selected.status.value}")
    print(f"Run log: {overview.path}")
    if not outcome.ok:
        return EXIT_RUN_FAILED
    if selected.status.value == "Venter ved kontrollpunkt":
        return EXIT_WAITING
    return EXIT_OK


def _continue(path: Path, *, job_id: str) -> int:
    loaded = _load(path)
    selected = loaded.batch.get(job_id)
    if selected is None:
        print(f"ERROR: Jobb-ID finnes ikke i jobblisten: {job_id}", file=sys.stderr)
        return EXIT_NOT_FOUND
    return _continue_one(path, loaded, selected)


def _run(path: Path, *, allow_rerun: bool, job_id: str | None = None) -> int:
    loaded = _load(path)

    if job_id:
        selected = loaded.batch.get(job_id)
        if selected is None:
            print(f"ERROR: Jobb-ID finnes ikke i jobblisten: {job_id}", file=sys.stderr)
            return EXIT_NOT_FOUND
        return _run_one(path, loaded, selected, allow_rerun=allow_rerun)

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
            return _run(args.joblist, allow_rerun=args.rerun, job_id=args.job_id)
        if args.object == "jobs" and args.action == "continue":
            return _continue(args.joblist, job_id=args.job_id)
    except JobListFormatError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_PREFLIGHT
    parser.error("Unsupported command")
    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
