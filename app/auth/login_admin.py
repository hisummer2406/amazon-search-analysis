# login_page.py
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

auth_router = APIRouter()

@auth_router.get("/admin/login")
async def login_page():
    """登录页面路由"""

    # 简单的登录页面HTML
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>系统登录</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { 
                margin: 0; 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background-image: url('https://picsum.photos/id/180/1920/1080');
                background-size: cover;
                background-position: center;
                background-attachment: fixed;                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .login-container {
                background: white;
                padding: 2rem;
                border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                width: 100%;
                max-width: 400px;
            }
            .form-group {
                margin-bottom: 1rem;
            }
            label {
                display: block;
                margin-bottom: 0.5rem;
                font-weight: 500;
            }
            input {
                width: 100%;
                padding: 0.75rem;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
            }
            button {
                width: 100%;
                padding: 0.75rem;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                cursor: pointer;
            }
            button:hover { background: #0056b3; }
            .header {
                text-align: center;
                margin-bottom: 2rem;
            }
            .logo {
                height: 50px;
                margin-bottom: 1rem;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="header">
                <img src="/static/amazon_logo.png" alt="Logo" class="logo">
                <h2>亚马逊数据分析系统</h2>
            </div>
            <form id="loginForm">
                <div class="form-group">
                    <label for="username">用户名</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="password">密码</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit">登录</button>
            </form>
        </div>
        <script>
            document.getElementById('loginForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        username: formData.get('username'),
                        password: formData.get('password')
                    })
                });
                const result = await response.json();
                if (result.status === 0) {
                    localStorage.setItem('access_token', result.data.access_token);
                    window.location.href = '/admin/';
                } else {
                    alert(result.msg || '登录失败');
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
