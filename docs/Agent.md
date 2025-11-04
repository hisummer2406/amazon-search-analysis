# 📇 项目速记卡 - 亚马逊关键词分析系统

> 🎯 **一句话描述**：专业的亚马逊搜索词数据分析平台，支持GB级CSV文件处理和多维度数据分析

---

## 🏷️ 基础信息

| 项目 | 信息 |
|-----|------|
| **项目名称** | 亚马逊关键词分析系统 (Amazon Search Analysis) |
| **项目类型** | 数据分析平台 (B2B SaaS) |
| **核心价值** | 亚马逊卖家搜索词排名监控、趋势分析、竞品洞察 |
| **技术栈** | FastAPI + PostgreSQL + Amis + Pandas |
| **部署方式** | Docker 容器化 |
| **数据规模** | 千万级记录，GB级文件处理 |

---

## 🎯 核心功能（5个）

```
1. 📊 数据分析  → 排名趋势图、多维度筛选、数据导出
2. 📁 文件上传  → GB级CSV、分块上传、多进程处理
3. 🔍 智能搜索  → 15+筛选维度、实时查询、秒级响应
4. 👥 用户管理  → 多用户系统、权限控制、JWT认证
5. ⚡ 性能优化  → 批量UPSERT、连接池、索引优化
```

---

## 🏗️ 技术架构（3层）

```
┌─────────────────────────────────────────┐
│  前端层: Amis UI (低代码)                 │
│  └─ 数据查询 / 文件上传 / 用户管理         │
├─────────────────────────────────────────┤
│  应用层: FastAPI (异步)                   │
│  ├─ auth/     (JWT认证)                  │
│  ├─ analysis/ (数据分析)                 │
│  ├─ upload/   (文件处理)                 │
│  └─ user/     (用户管理)                 │
├─────────────────────────────────────────┤
│  数据层: PostgreSQL 15                    │
│  ├─ user_center (用户表)                 │
│  ├─ amazon_origin_search_data (主数据表)│
│  └─ import_batch_records (导入记录表)    │
└─────────────────────────────────────────┘
```

---

## 📊 数据模型（核心表）

### amazon_origin_search_data（分析数据表）

```python
核心字段：
├─ keyword (关键词)
├─ 日排名数据
│  ├─ current_rangking_day (当前日排名)
│  ├─ ranking_change_day (日变化)
│  └─ ranking_trend_day (7天趋势, JSONB)
├─ 周排名数据
│  ├─ current_rangking_week (当前周排名)
│  └─ ranking_change_week (周变化)
├─ Top 3 产品信息
│  ├─ top_brand/category/asin/title
│  ├─ top_product_click_share (点击份额%)
│  └─ top_product_conversion_share (转化份额%)
└─ 状态标识
   ├─ is_new_day (是否日新品)
   └─ is_new_week (是否周新品)

关键特性：
✓ keyword 字段唯一索引（自动去重）
✓ ranking_trend_day 使用JSONB存储历史（最多7天）
✓ UPSERT策略：同日更新/跨日追加
```

---

## 🔄 核心业务流程

### 文件上传处理流程

```
用户上传CSV
    ↓
文件验证（格式/大小/结构）
    ↓
判断文件大小 < 100MB?
    ↓                    ↓
   是                    否
    ↓                    ↓
单线程处理            多进程处理
分批UPSERT           文件分片 → 并行处理
    ↓                    ↓
    └────────┬──────────┘
             ↓
    PostgreSQL UPSERT
    ├─ 同日同关键词 → 更新
    └─ 跨日新关键词 → 插入+追加趋势
             ↓
    实时进度反馈
             ↓
    处理完成通知
```

### 数据查询流程

```
用户输入搜索条件
    ↓
构建动态SQL查询
├─ 基础筛选：keyword/brand/category/asin
├─ 范围筛选：ranking/change/share
└─ 布尔筛选：is_new_day/is_new_week
    ↓
应用排序和分页
    ↓
PostgreSQL查询（带索引优化）
    ↓
数据格式化
├─ 计算转化率 (conversion_share / click_share)
└─ 格式化日期
    ↓
返回JSON响应
```

---

## ⚙️ 关键配置

```python
# 性能配置
BATCH_SIZE = 5000              # 批处理大小
MINIBATCH_SIZE = 1000          # 小批次大小
MAX_WORKERS = 4                # 工作进程数
MULTIPROCESSING_THRESHOLD_MB = 100  # 多进程阈值

# 数据库连接池
DB_POOL_SIZE = 100             # 连接池大小
DB_MAX_OVERFLOW = 150          # 最大溢出连接
DB_POOL_TIMEOUT = 60           # 连接超时(秒)

# 文件处理
MAX_FILE_SIZE = 3GB            # 最大文件大小
FILE_SPLIT_LINES = 50000       # 文件分片行数
```

---

## 🚀 快速启动（3步）

```bash
# 1. 部署
./deploy.sh

# 2. 访问
http://localhost:8000

# 3. 登录
admin / pwd123
```

---

## 📂 目录结构（精简版）

```
amazon-search-analysis/
├── app/
│   ├── auth/           # JWT认证、中间件
│   ├── table/
│   │   ├── analysis/   # CRUD + Service + API
│   │   ├── search/     # 搜索组件
│   │   └── upload/     # CSV处理 + 上传API
│   └── user/           # 用户CRUD + API
├── static/             # 前端资源
├── uploads/            # 上传目录
├── main.py             # 应用入口
├── config.py           # 配置管理
├── database.py         # 数据库连接
└── docker-compose.yml  # 容器编排
```

---

## 🔑 核心技术实现

### 1. 大文件处理
```python
策略：
- 文件 < 100MB → 单线程分批处理
- 文件 ≥ 100MB → 多进程并行处理
  ├─ 按行数分片 (50000行/片)
  ├─ ProcessPoolExecutor 并行
  └─ 独立数据库会话

优化：
✓ 分块读取（避免内存溢出）
✓ 批量UPSERT（减少IO次数）
✓ 连接池复用（提升并发性能）
```

### 2. 数据去重策略
```sql
INSERT INTO ... VALUES (...)
ON CONFLICT (keyword) DO UPDATE SET
  -- 同日数据：更新当前排名
  -- 跨日数据：追加历史趋势（最多7天）
  ranking_trend_day = CASE 
    WHEN 同一天 THEN 更新当天排名
    ELSE 追加新数据 + 保留最近6天
  END
```

### 3. 查询优化
```python
优化点：
✓ keyword 字段建立B-tree索引
✓ report_date_day 字段建立索引
✓ 使用count()子查询优化总数统计
✓ 分页查询offset+limit
✓ 默认过滤：排除关键词包含品牌词的记录
```

---

## 📊 API接口（核心）

| 接口 | 方法 | 功能 | 参数 |
|-----|------|-----|------|
| `/api/auth/login` | POST | 用户登录 | username, password |
| `/api/analysis/search` | GET | 数据查询 | 15+筛选参数 + 分页 |
| `/api/analysis/categories` | GET | 获取类目 | - |
| `/api/upload/startChunkApi` | POST | 开始分块上传 | filename, data_type |
| `/api/upload/chunkApi` | POST | 上传分块 | key, partNumber, file |
| `/api/upload/finishChunkApi` | POST | 完成上传 | key, uploadId |
| `/api/user/list` | GET | 用户列表 | 分页 + 筛选 |

---

## 🎨 前端技术

```javascript
Amis低代码框架：
├─ CRUD组件（数据表格）
├─ Form组件（搜索表单）
├─ Dialog组件（弹窗）
├─ Upload组件（文件上传）
└─ Chart组件（ECharts趋势图）

特点：
✓ 配置即界面（JSON Schema）
✓ 内置分页、排序、筛选
✓ 支持分块上传（10MB/块）
```

---

## 🔐 认证机制

```python
流程：
用户登录
  ↓
验证用户名密码（BCrypt加密）
  ↓
生成JWT Token（24小时有效）
  ↓
前端存储到localStorage
  ↓
API请求携带 Authorization: Bearer <token>
  ↓
中间件验证Token
  ↓
解析用户信息到request.state.current_user
```

---

## ⚠️ 注意事项

### 性能瓶颈
```
1. 大文件上传 → 使用分块上传 + 后台处理
2. 批量插入 → 使用UPSERT + 小批次提交
3. 并发查询 → 连接池 + 索引优化
4. 内存占用 → 分块读取 + 流式处理
```

### 数据完整性
```
1. UPSERT确保keyword唯一性
2. 事务管理防止数据不一致
3. 导入批次记录跟踪处理状态
4. 错误日志记录便于排查
```

### 安全考虑
```
1. 密码BCrypt加密存储
2. JWT Token过期机制
3. 中间件拦截未授权请求
4. 超级管理员不能被禁用
```

---

## 🐛 常见问题速查

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| 上传超时 | 文件过大 | 增加Nginx超时配置 |
| 处理慢 | 进程数不足 | 调整MAX_WORKERS |
| 查询慢 | 索引缺失 | 检查数据库索引 |
| 连接失败 | 连接池耗尽 | 增加DB_POOL_SIZE |
| 内存溢出 | 批次过大 | 减小BATCH_SIZE |

---

## 📈 性能指标

```
处理能力：
├─ 单文件：最大 3GB
├─ 处理速度：约 10万条/分钟（4核）
├─ 查询响应：< 1秒（千万级数据）
└─ 并发支持：100+ 连接

数据规模：
├─ 单表记录：千万级
├─ 历史趋势：7天JSONB存储
└─ 文件上传：支持GB级别
```

---

## 🔄 数据流转

```mermaid
上传CSV → 验证格式 → 判断大小 → 处理策略选择
                                    ↓
                          [单线程 or 多进程]
                                    ↓
                            分批读取CSV
                                    ↓
                            数据清洗映射
                                    ↓
                        批量UPSERT到PostgreSQL
                                    ↓
                            自动去重合并
                                    ↓
                            前端实时查询 → 可视化展示
```

---

## 💡 设计亮点

1. **智能去重**：keyword唯一索引 + UPSERT自动合并
2. **趋势存储**：JSONB存储7天历史，灵活高效
3. **分片处理**：大文件自动分片 + 多进程并行
4. **连接优化**：连接池 + 预检机制 + 自动重连
5. **进度反馈**：实时更新处理进度到数据库
6. **低代码UI**：Amis配置化开发，快速迭代

---

## 🎓 学习要点

**新手关注**：
- FastAPI路由和依赖注入
- SQLAlchemy ORM和查询构建
- Pandas数据处理
- Docker容器化部署

**进阶关注**：
- 多进程数据处理架构
- PostgreSQL UPSERT策略
- 数据库连接池优化
- JWT认证中间件

**高级关注**：
- 大文件流式处理
- 批量操作性能优化
- JSONB字段高级查询
- 系统监控和日志

---

## 📞 快速联系

- **技术支持**: stone_summer24
- **对标网站**: https://8b164h4196.vicp.fun/ (zhangxiaoxiao / 1)
- **文档**: README.md

---

<div align="center">

**🚀 3分钟快速上手 | ⚡ 秒级响应查询 | 📊 专业数据分析**

最后更新: 2024-01

</div>