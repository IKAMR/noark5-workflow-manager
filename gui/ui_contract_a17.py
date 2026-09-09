"""Stable a17 UI contract.

Tests should assert these semantic values instead of private widget/grid
implementation details. Runtime code may change layout technique without
forcing unrelated regression tests to be rewritten.
"""

HEADER_ACTIONS = ("Mapper", "Jobber", "Setup", "A-", "A+", "?")
HEADER_LAYOUT_KIND = "dedicated-action-frame"
SETUP_TITLE = "Setup"
TEMP_DIRECTORY_IN_SETUP = True
RESULTS_ACTION_LOCATION = "run-log"
