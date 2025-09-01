import unittest
from app.auth.auth_middleware import AdminAuthMiddleware

class TestAdminAuthMiddleware(unittest.TestCase):
    def middleware(self):
        # 创建中间件实例，不需要实际的app参数
        return AdminAuthMiddleware(app=None)

    def test_exclude_paths_return_false(self, middleware):
        # 测试排除路径返回False
        exclude_paths = [
            ("/admin/login", False),
            ("/api/auth/login", False),
            ("/static/css/style.css", False),
            ("/docs", False),
            ("/", False)
        ]
        for path, expected in exclude_paths:
            assert middleware._needs_auth(path) == expected, f"Failed for path: {path}"

    def test_protected_paths_return_true(self, middleware):
        # 测试保护路径返回True
        protected_paths = [
            ("/api/analysis/search", True),
            ("/api/user/list", True),
            ("/admin/user", True),
            ("/admin/analysis", True)
        ]
        for path, expected in protected_paths:
            assert middleware._needs_auth(path) == expected, f"Failed for path: {path}"

    def test_partial_matches(self, middleware):
        # 测试部分匹配情况
        partial_cases = [
            ("/admin/login/123", False),  # 部分匹配排除路径
            ("/admin/user/profile", True),  # 部分匹配保护路径
            ("/api/auth/login/validate", False),  # 部分匹配排除路径
            ("/api/analysis/search/1", True)  # 部分匹配保护路径
        ]
        for path, expected in partial_cases:
            assert middleware._needs_auth(path) == expected, f"Failed for path: {path}"

    def test_other_paths_return_false(self, middleware):
        # 测试既不在排除也不在保护列表中的路径
        assert middleware._needs_auth("/unknown/path") is False
        assert middleware._needs_auth("/api/public/data") is False
        assert middleware._needs_auth("/admin/dashboard") is False