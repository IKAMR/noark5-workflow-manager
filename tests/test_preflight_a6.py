import unittest
from pathlib import Path

from noark5_workflow.core.job import Job, JobStatus
from noark5_workflow.core.preflight import JobPreflight


class PreflightA6Tests(unittest.TestCase):
    def setUp(self):
        self.preflight = JobPreflight()

    def job(self, job_id, output=None):
        return Job(job_id=job_id, source_root=Path(job_id), output_root=Path(output) if output else None, workflow_ids=["one", "two"])

    def test_stale_running_is_safely_normalized(self):
        job = self.job("JOB-001")
        job.status = JobStatus.RUNNING
        job.next_operation_index = 1
        changes = self.preflight.normalize_job(job)
        self.assertEqual(job.status, JobStatus.READY)
        self.assertEqual(job.next_operation_index, 0)
        self.assertEqual(changes[0].code, "stale_running")

    def test_invalid_waiting_cursor_is_safely_normalized(self):
        job = self.job("JOB-001")
        job.status = JobStatus.WAITING
        job.next_operation_index = 99
        changes = self.preflight.normalize_job(job)
        self.assertEqual(job.status, JobStatus.READY)
        self.assertEqual(job.next_operation_index, 0)
        self.assertIn("invalid_cursor", [change.code for change in changes])

    def test_duplicate_outputs_are_reported_without_gui(self):
        jobs = [self.job("JOB-001", "same-output"), self.job("JOB-002", "same-output")]
        conflicts = self.preflight.check_outputs(jobs)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].first_job_id, "JOB-001")
        self.assertEqual(conflicts[0].second_job_id, "JOB-002")

    def test_rerun_jobs_are_identified_but_not_approved(self):
        completed = self.job("JOB-001")
        completed.status = JobStatus.OK
        ready = self.job("JOB-002")
        reruns = self.preflight.find_reruns([completed, ready])
        self.assertEqual([job.job_id for job in reruns], ["JOB-001"])
        self.assertEqual(completed.status, JobStatus.OK)

    def test_report_combines_checks(self):
        completed = self.job("JOB-001", "same-output")
        completed.status = JobStatus.OK
        duplicate = self.job("JOB-002", "same-output")
        report = self.preflight.check([completed, duplicate])
        self.assertFalse(report.ok)
        self.assertTrue(report.rerun_required)
        self.assertEqual(len(report.output_conflicts), 1)

    def test_core_preflight_has_no_gui_dependency(self):
        path = Path(__file__).resolve().parents[1] / "noark5_workflow" / "core" / "preflight.py"
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("tkinter", text)
        self.assertNotIn("messagebox", text)


if __name__ == "__main__":
    unittest.main()
