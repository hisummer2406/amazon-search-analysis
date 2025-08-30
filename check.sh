# 在容器中执行以下命令来诊断问题

# 1. 检查当前的环境变量
echo "=== 检查环境变量 ==="
env | grep -i page
env | grep -E "(DEFAULT_PAGE_SIZE|MAX_PAGE_SIZE|default_page_size|max_page_size)"

# 2. 检查 .env 文件内容
echo "=== 检查 .env 文件 ==="
if [ -f ".env" ]; then
    cat .env | grep -i page
else
    echo ".env 文件不存在"
fi

# 3. 检查 .env.example 文件内容
echo "=== 检查 .env.example 文件 ==="
if [ -f ".env.example" ]; then
    cat .env.example | grep -i page
else
    echo ".env.example 文件不存在"
fi

# 4. 检查当前 config.py 的内容
echo "=== 检查 config.py 中的 Config 类 ==="
grep -A 5 "class Config:" config.py

# 5. 尝试直接导入配置看具体错误
python3 -c "
try:
    from config import settings
    print('配置加载成功')
    print(f'APP_NAME: {settings.APP_NAME}')
except Exception as e:
    print(f'配置加载失败: {e}')
    import traceback
    traceback.print_exc()
"
