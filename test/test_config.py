import unittest

from config import Settings


class TestSettings(unittest.TestCase):
    def test_env_file(self):
        """测试默认配置值"""
        settings = Settings()
        print(settings.APP_NAME)
        self.assertEqual(settings.DEBUG, True)
