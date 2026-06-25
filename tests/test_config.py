import json
import os
import tempfile
import unittest

from keyword_extractor import load_config


class LoadConfigTests(unittest.TestCase):
    def test_uses_environment_overrides(self):
        """Check that environment variables override JSON config values."""
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as config_file:
            json.dump({"model": "from-file", "max_tokens": 123}, config_file)
            config_path = config_file.name

        original_model = os.environ.get("TRANSLATOR_MODEL")
        original_tokens = os.environ.get("TRANSLATOR_MAX_TOKENS")
        try:
            os.environ["TRANSLATOR_MODEL"] = "from-env"
            os.environ["TRANSLATOR_MAX_TOKENS"] = "456"

            config = load_config(config_path)

            self.assertEqual(config["model"], "from-env")
            self.assertEqual(config["max_tokens"], 456)
        finally:
            if original_model is None:
                os.environ.pop("TRANSLATOR_MODEL", None)
            else:
                os.environ["TRANSLATOR_MODEL"] = original_model

            if original_tokens is None:
                os.environ.pop("TRANSLATOR_MAX_TOKENS", None)
            else:
                os.environ["TRANSLATOR_MAX_TOKENS"] = original_tokens

            os.unlink(config_path)

    def test_keeps_api_key_as_environment_variable_name(self):
        """Check that the config points to an env var instead of storing a secret."""
        config = load_config()

        self.assertEqual(config["api_key_env"], "DEEPSEEK_API_KEY")
        self.assertFalse(config["api_key_env"].startswith("sk-"))


if __name__ == "__main__":
    unittest.main()
