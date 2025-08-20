import unittest
from app.config import Settings

class TestSettings(unittest.TestCase):
    def test_settings(self):
        settings = Settings()
        print(settings)
