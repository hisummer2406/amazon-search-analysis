# CLAUDE_ZH.md

此文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

这是一个基于 Python/FastAPI 构建的亚马逊关键词分析系统，能够处理大规模 CSV 数据（GB 级文件）、实时数据分析和可视化。系统支持多用户管理、JWT 认证和使用多进程技术的高性能数据处理。

## 系统架构

```
前端 (Amis UI) → 应用层 (FastAPI) → 数据层 (PostgreSQL)
                     ↓
            ┌────────┴────────┐
            ├─ 认证模块 (JWT)
            ├─ 数据分析接口
            ├─ 文件上传处理
            └─ 用户权限管理
```

**核心技术**: FastAPI + PostgreSQL + Pandas + 多进程处理

## 常见开发任务

### 运行应用程序

**本地开发:**
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动应用
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Docker 部署:**
```bash
# 使用脚本部署
chmod +x deploy.sh
./deploy.sh

# 或者使用 Docker Compose 手动部署
docker-compose up -d
```

### 测试

运行测试:
```bash
# 运行特定测试文件
python -m pytest test/

# 运行带覆盖率的测试
python -m pytest --cov=app test/
```

### 核心模块

1. **app/table/upload/** - 处理 CSV 文件上传，支持分块处理和大文件多进程处理
2. **app/table/analysis/** - 数据分析和搜索功能
3. **app/auth/** - 认证和授权（基于 JWT）
4. **app/user/** - 用户管理
5. **database.py** - 数据库连接和会话管理
6. **config.py** - 应用配置，使用 pydantic-settings

### 性能优化

关键性能特性:
- 大文件处理的多进程支持（GB 级 CSV 文件）
- 可配置批次大小的批处理
- 数据库连接池
- 内存效率的分块文件读取
- 长时间运行操作的进度监控

`.env` 中的配置参数:
```
BATCH_SIZE=5000          # 批处理大小
MAX_WORKERS=4            # 多进程工作数
DB_POOL_SIZE=100         # 数据库连接池大小
FILE_SPLIT_LINES=100000  # 每个文件分块的行数
```

## 项目结构

```
amazon-search-analysis/
├── app/                    # 应用主目录
│   ├── auth/              # 认证模块
│   ├── table/             # 数据模块
│   │   ├── analysis/      # 数据分析
│   │   ├── search/        # 搜索功能
│   │   └── upload/        # 文件上传
│   └── user/              # 用户模块
├── static/                # 静态文件
├── uploads/               # 上传目录
├── main.py                # 应用入口点
└── config.py              # 配置文件
```

## 数据库结构

关键表:
- `amazon_origin_search_data` - 主数据表，包含亚马逊搜索关键词和指标
- `import_batch_records` - 文件处理批次记录
- `user_center` - 用户管理表

## API 文档

访问地址:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 环境配置

创建 `.env` 文件，包含:
```
# 数据库配置
DATABASE_URL=postgresql://postgres:your_password@db:5432/amazon_db
DATABASE_URL_ASYNC=postgresql+asyncpg://postgres:your_password@db:5432/amazon_db
DATABASE_SCHEMA=analysis

# 安全配置（必须修改）
ADMIN_SECRET_KEY=<生成随机字符串>

# 性能配置
BATCH_SIZE=5000
MAX_WORKERS=4
FILE_SPLIT_LINES=100000
```