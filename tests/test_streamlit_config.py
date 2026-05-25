from __future__ import annotations

import unittest
from pathlib import Path


class StreamlitConfigTests(unittest.TestCase):
    def test_config_keeps_theme_and_polling_file_watcher(self):
        config = Path(".streamlit/config.toml").read_text(encoding="utf-8")

        self.assertIn("[server]", config)
        self.assertIn('fileWatcherType = "poll"', config)
        self.assertIn("runOnSave = true", config)
        self.assertIn("[theme]", config)
        self.assertIn('primaryColor = "#35F2FF"', config)
        self.assertIn("[theme.sidebar]", config)


if __name__ == "__main__":
    unittest.main()
