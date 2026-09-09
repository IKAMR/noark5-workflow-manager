from __future__ import annotations

import unittest

from gui.persistent_app_a18 import WorkflowApp


class A18SourceLogDedupTests(unittest.TestCase):
    def _app_without_tk(self):
        app = object.__new__(WorkflowApp)
        app._last_source_log_key = None
        return app

    def test_same_source_is_logged_only_once(self):
        app = self._app_without_tk()
        path = r"G:\arkiv-noark5\1502\uttrekk"
        self.assertTrue(app._source_log_changed(path))
        self.assertFalse(app._source_log_changed(path))
        self.assertFalse(app._source_log_changed(path.replace("\\", "/")))

    def test_real_source_change_is_logged(self):
        app = self._app_without_tk()
        self.assertTrue(app._source_log_changed(r"G:\source\A"))
        self.assertTrue(app._source_log_changed(r"G:\source\B"))
        self.assertFalse(app._source_log_changed(r"g:\source\b"))


if __name__ == "__main__":
    unittest.main()
