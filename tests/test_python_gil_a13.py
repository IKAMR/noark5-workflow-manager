from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PythonGilA13Tests(unittest.TestCase):
    def test_test_bat_enables_gil_before_python(self):
        text = (ROOT / "test.bat").read_text(encoding="utf-8")
        self.assertLess(text.index('set "PYTHON_GIL=1"'), text.index("py tests"))

    def test_start_bat_enables_gil_before_python(self):
        text = (ROOT / "start.bat").read_text(encoding="utf-8")
        self.assertLess(text.index('set "PYTHON_GIL=1"'), text.index("py main.py"))

    def test_cli_launcher_generated_with_gil_enabled(self):
        text = (ROOT / "install.bat").read_text(encoding="utf-8")
        self.assertIn('echo set "PYTHON_GIL=1"', text)


if __name__ == "__main__":
    unittest.main()
