import tempfile
import unittest
from pathlib import Path

from noark5_workflow.core.output_lock import OutputLock, OutputLockedError


class OutputLockTests(unittest.TestCase):
    def test_second_lock_on_same_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = OutputLock(root, "JOB-001")
            second = OutputLock(root, "JOB-002")
            first.acquire()
            try:
                with self.assertRaises(OutputLockedError):
                    second.acquire()
            finally:
                first.release()
            self.assertFalse((root / OutputLock.FILENAME).exists())

    def test_lock_can_be_acquired_after_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with OutputLock(root, "JOB-001"):
                self.assertTrue((root / OutputLock.FILENAME).exists())
            with OutputLock(root, "JOB-002"):
                self.assertTrue((root / OutputLock.FILENAME).exists())


if __name__ == "__main__":
    unittest.main()
