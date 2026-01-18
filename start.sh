#!/bin/bash
# 生产环境启动脚本 - Uvicorn 多进程模式

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Amazon Search Analysis - Production${NC}"
echo -e "${GREEN}======================================${NC}"

# 检查 .env 文件
if [ ! -f .env ]; then
    echo -e "${RED}错误: .env 文件不存在，请先创建${NC}"
    exit 1
fi

# 加载环境变量
export $(grep -v '^#' .env | xargs)

# 检查必需的环境变量
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}错误: DATABASE_URL 未设置${NC}"
    exit 1
fi

# 显示配置信息
echo -e "${YELLOW}当前配置:${NC}"
echo "  APP_NAME: ${APP_NAME}"
echo "  DEBUG: ${DEBUG}"
echo "  DB_POOL_SIZE: ${DB_POOL_SIZE:-8}"
echo "  DB_MAX_OVERFLOW: ${DB_MAX_OVERFLOW:-12}"
echo "  BATCH_SIZE: ${BATCH_SIZE:-10000}"
echo "  MINIBATCH_SIZE: ${MINIBATCH_SIZE:-500}"
echo ""
echo -e "${GREEN}启动 Uvicorn 服务器 (4 workers)...${NC}"

# Uvicorn 多进程模式（4核 ECS 推荐）
# 注意：Uvicorn 的 workers 是多进程模式，不需要 Gunicorn
exec uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --timeout-keep-alive 600 \
  --limit-concurrency 1000 \
  --loop uvloop \
  --log-level info \
  --no-access-log