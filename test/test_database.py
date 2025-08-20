import logging
from sqlalchemy import text
import unittest

from database import engine, async_engine


class TestDatabase(unittest.TestCase):
    def test_sync_db(self):
        """测试同步数据库连接"""
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                self.assertEqual(result.scalar(), 1)
            logging.info("✅ 同步数据库连接测试成功")
        except Exception as e:
            self.fail(f"数据库连接测试失败: {e}")

class TestAsyncDatabase(unittest.IsolatedAsyncioTestCase):
    async def test_async_db(self):
        """测试异步数据库连接"""
        try:
            async with async_engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                self.assertEqual(result.scalar(), 1)
            logging.info("✅ 异步数据库连接测试成功")
        except Exception as e:
            self.fail(f"数据库连接测试失败: {e}")

if __name__ == '__main__':
    unittest.main()