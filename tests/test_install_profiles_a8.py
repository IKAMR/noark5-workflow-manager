from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_dependency_profiles_exist_and_gui_is_separate():
    core = read("requirements-core.txt").lower()
    gui = read("requirements-gui.txt").lower()
    assert "customtkinter" not in core
    assert "customtkinter" in gui


def test_install_supports_all_gui_cli_and_state():
    text = read("install.bat").lower()
    for mode in ("all", "gui", "cli"):
        assert f'"{mode}"' in text
    assert "install-state.json" in text
    assert "current_gui" in text
    assert "current_cli" in text
    assert "migrering fra a7" in text


def test_deinstall_requires_ja_and_preserves_core_when_needed():
    text = read("deinstall.bat").lower()
    assert "skriv ja eller nei" in text
    assert '=="ja"' in text
    assert "new_core" in text
    assert 'if "%new_gui%"=="1" set "new_core=1"' in text
    assert 'if "%new_cli%"=="1" set "new_core=1"' in text


def test_deinstall_does_not_remove_shared_dependencies():
    text = read("deinstall.bat").lower()
    assert "generelle python-pakker" in text
    assert "pip uninstall -y noark5-workflow-manager" in text
    assert "pip uninstall -y lxml" not in text
    assert "pip uninstall -y psutil" not in text
    assert "pip uninstall -y customtkinter" not in text
