# 🚀 亚马逊关键词分析系统

> 专业的亚马逊搜索词数据分析平台，支持GB级大文件处理、实时数据分析和可视化展示

---

## ✨ 功能特性

- **📊 数据分析**：多维度筛选、排名趋势图、自定义导出
- **📁 大文件处理**：支持GB级CSV上传、智能分块、多进程处理
- **🔍 智能搜索**：15+维度组合查询、实时数据更新
- **👥 权限管理**：多用户系统、JWT认证、细粒度权限
- **⚡ 高性能**：千万级数据秒级查询、批量UPSERT去重

---

## 🏗️ 技术架构

```
前端 (Amis UI) → 应用层 (FastAPI) → 数据层 (PostgreSQL)
                     ↓
            ┌────────┴────────┐
            ├─ 认证模块 (JWT)
            ├─ 数据分析接口
            ├─ 文件上传处理
            └─ 用户权限管理
```

**核心技术**：FastAPI + PostgreSQL + Pandas + 多进程处理

---

## 🚀 快速开始

### 环境要求

- Docker 20.10+ / Docker Compose 2.0+
- 磁盘空间 20GB+ / 内存 8GB+

### 一键部署

```bash
# 1. 克隆项目
git clone <project-repo>
cd amazon-search-analysis

# 2. 执行部署
chmod +x deploy.sh
./deploy.sh

# 3. 访问系统
浏览器访问: http://localhost:8000
默认账号: admin / pwd123
```

---

## 📦 生产环境部署

### 环境配置

创建 `.env` 文件：

```bash
# 数据库配置
DATABASE_URL=postgresql://postgres:your_password@db:5432/amazon_db
DATABASE_SCHEMA=analysis

# 安全配置（必须修改）
ADMIN_SECRET_KEY=<生成随机字符串>

# 性能配置
BATCH_SIZE=5000
MAX_WORKERS=4
```

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    client_max_body_size 3G;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_read_timeout 600;
    }
}
```

---

## 📖 使用指南

### 数据上传

1. **文件格式**：亚马逊搜索词报告CSV格式
2. **上传方式**：点击"上传日数据"或"上传周数据"
3. **文件命名**：建议包含日期，如 `amazon_2024-01-15.csv`

### 数据查询

**基础搜索**：关键词、品牌、类目、ASIN

**高级筛选**（点击"高级搜索"）：
- 排名范围（日排名/周排名）
- 变化趋势（日变化/周变化）
- 数据指标（点击份额/转化份额/转化率）
- 状态筛选（日新品/周新品）

### 用户管理

进入"用户管理"页面 → "新增用户" → 填写信息（用户名/密码/状态）

---

## 💻 开发指南

### 本地开发

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动应用
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 项目结构

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
├── main.py                # 应用入口
└── config.py              # 配置文件
```

### API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

### 上传问题

**Q: 文件上传失败？**
- 检查文件格式（CSV）
- 检查文件大小限制（3GB）
- 检查磁盘空间

**Q: 处理速度慢？**
- 调整 `MAX_WORKERS`（建议4-8）
- 调整 `BATCH_SIZE`（建议5000）

### 性能优化

```bash
# .env 配置
BATCH_SIZE=5000          # 批处理大小
MAX_WORKERS=4            # 工作进程数
DB_POOL_SIZE=100         # 连接池大小
```

---

## 🔧 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 后端 | Python / FastAPI | 3.11+ / 0.104+ |
| 数据库 | PostgreSQL | 15+ |
| 数据处理 | Pandas / SQLAlchemy | 2.1+ / 2.0+ |
| 前端 | Amis UI / ECharts | 最新版 |
| 基础设施 | Docker / Nginx | 20.10+ / 1.20+ |

---

## 📝 常用命令

```bash

uvicorn main:app --host 0.0.0.0 --port 8000

# 重启应用容器（最常用） 
docker-compose restart app

# 进入容器
docker exec -it amazon-search-analysis-app-1 /bin/bash

# 重启容器应用新配置 
docker-compose down 
docker-compose up -d

# 监控日志
docker-compose logs -f app | grep upload

使用 du 命令查看目录占用空间
du 命令可以查看文件或目录的磁盘使用情况。

`du -ah /path/to/search | sort -rh | head -n 20`

* -a：显示所有文件和目录的大小。
* -h：以人类可读的方式显示文件大小（例如 MB、GB）。
* sort -rh：按文件大小降序排序。
* head -n 20：显示前 20 个最大文件或目录。

# Nginx 日志
    access_log /var/log/nginx/amazon-analysis.access.log;
    error_log /var/log/nginx/amazon-analysis.error.log;

# PG 配置

ECS Alibaba Cloud Linux 3.2104 LTS 64位 4 核（vCPU）8 GiB
RDS PostgreSQL15.0 2C4G默认连接数 400
```

---

## 📞 参考资料

### 对标网站
- 网站: [https://8b164h4196.vicp.fun/](https://8b164h4196.vicp.fun/)
- 账号: zhangxiaoxiao / 密码: 1

### 紫鸟浏览器
- 公司: 郑州采参堂电子商务有限公司
- 用户: 开发 / 密码: KF112233@

### 相关文档
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Amis 文档](https://docs.amis.work/zh/)

---

<div align="center">

**© 2025 亚马逊关键词分析系统 | 专业·高效·智能**

技术支持: stone_summer24

</div>