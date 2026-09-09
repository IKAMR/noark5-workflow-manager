from __future__ import annotations

import json
import tempfile
import unittest
import uuid
from pathlib import Path

from app.user_profile import FILE_TYPE, load_user_profile, save_user_profile, validate_profile_fields


class UserProfileA18Tests(unittest.TestCase):
    def test_profile_is_persisted_with_stable_generated_user_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "user-profile.json"
            first = save_user_profile("Test User", "tester", "test@example.org", path=path)
            uuid.UUID(first.user_id)
            loaded = load_user_profile(path)
            self.assertEqual(first, loaded)
            changed = save_user_profile("Test User Two", "tester", "test2@example.org", path=path)
            self.assertEqual(first.user_id, changed.user_id)
            self.assertEqual("test2@example.org", changed.email)

    def test_profile_file_has_explicit_type_and_no_repository_config_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "user-profile.json"
            save_user_profile("Test User", "tester", "test@example.org", path=path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(FILE_TYPE, payload["file_type"])
            self.assertEqual(1, payload["format_version"])
            self.assertIn("user_id", payload["profile"])

    def test_visible_fields_are_required(self):
        for values in (("", "u", "u@example.org"), ("Name", "", "u@example.org"), ("Name", "u", "bad")):
            with self.assertRaises(ValueError):
                validate_profile_fields(*values)

    def test_username_contract_is_server_safe(self):
        validate_profile_fields("Name", "user.name-_1", "u@example.org")
        with self.assertRaises(ValueError):
            validate_profile_fields("Name", "user name", "u@example.org")

    def test_log_identity_contains_stable_id_and_three_profile_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = save_user_profile("Test User", "tester", "test@example.org", path=Path(tmp)/"p.json")
            self.assertEqual({"user_id", "username", "name", "email"}, set(profile.log_identity()))


if __name__ == "__main__":
    unittest.main()
