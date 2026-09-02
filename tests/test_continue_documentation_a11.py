import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ContinueDocumentationA11Tests(unittest.TestCase):
    def test_cli_documents_public_continue_command(self):
        text = (ROOT / "docs" / "CLI.md").read_text(encoding="utf-8")
        self.assertIn("n5wf jobs continue <file.n5jobs> --job <job-id>", text)
        self.assertIn("per v0.1.2-a11", text)
        self.assertNotIn("egen `continue`- eller `stop`-kommando er ikke implementert", text)

    def test_interface_marks_continue_as_implemented_shared_contract(self):
        text = (ROOT / "docs" / "INTERFACE.md").read_text(encoding="utf-8")
        self.assertIn("Fra v0.1.2-a11", text)
        self.assertIn("JobRunner.continue_job()", text)
        self.assertIn("n5wf jobs continue <file.n5jobs> --job <job-id>", text)

    def test_jobs_and_batches_documents_same_gui_cli_contract(self):
        text = (ROOT / "docs" / "JOBS-AND-BATCHES.md").read_text(encoding="utf-8")
        self.assertIn("JobRunner.continue_job()", text)
        self.assertIn("GUI-et bruker den samme `continue_job()`-kontrakten", text)
        self.assertIn("n5wf jobs continue", text)


if __name__ == "__main__":
    unittest.main()
