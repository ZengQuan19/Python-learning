# Python 学习练习

大一上学期（2026 秋）的学习记录，从零开始学 Python 数据分析与 SQL，最后做一个网页版《数据分析 Agent》。

## 内容

- `SQL/`：SQL 基础 01–07（SELECT、GROUP BY、JOIN、CASE、窗口函数、日期函数、面试真题）
- `Net/`：第一次 HTTP 请求
- `Agent/`：《数据分析 Agent》网页工程（v1 Flask+MySQL → v2 接 LLM → v3 工具调用+多轮记忆）
- `*.py`：早期 NumPy / pandas / sklearn 练习

## 怎么跑（早期练习脚本）

需要 Python 3.13 + pandas + scikit-learn。

```bash
python SQL/01_select.py
```

## Agent/：数据分析 Agent

**当前进度：v2 已完成** ✅
在浏览器里用中文提问，大模型自己写 SQL 去查库，页面显示 SQL、结果表格和一句中文解释。

### 目录结构

```
Agent/
├─ app.py            # 入口：Flask 路由 + 页面 + 启动自检
├─ qa.py             # 编排层：问题 -> SQL -> 审核 -> 执行 -> 解释
├─ llm.py            # 模型层：调 DeepSeek（ask_sql / explain）
├─ db.py             # 数据层：连库、查询、SQL 只读安全闸
├─ llm_config.py     # 【不入库】API key 配置（已被 .gitignore 排除）
├─ templates/
│  └─ index.html     # 首页模板（输入框 + SQL 块 + 结果表格 + 结论）
└─ static/
   └─ style.css      # 样式表
```

### 运行

```bash
# 1. 装依赖（只需一次）
.venv\Scripts\python.exe -m pip install flask pymysql requests

# 2. 配置模型 key（只做一次，不会进仓库）
#    复制/新建 Agent/llm_config.py，填入：
#        API_KEY = "sk-你的key"
#        BASE_URL = "https://api.deepseek.com"
#        MODEL = "deepseek-flash"

# 3. 启动服务
.venv\Scripts\python.exe Agent\app.py
```

浏览器打开 http://127.0.0.1:5000 ，输入「哪个用户花钱最多」并提交。
一次提问要等 2~10 秒：程序会调两次模型（第一次写 SQL，第二次解释结果）。

### 数据流

```
浏览器 GET /?q=哪个用户花钱最多
   │
   ▼
qa.run_question()
   ├─ llm.ask_sql()      问题 + 表结构 -> 模型 -> SQL 文本
   ├─ db.check_sql()     安全审核（只读白名单，见下）
   ├─ db.run_select()    MySQL 执行 -> list[dict]
   └─ llm.explain()      问题 + SQL + 结果 -> 模型 -> 中文解释
   │
   ▼
templates/index.html 渲染：SQL 代码块 + 结果表格 + 结论
```

### 安全设计（v2 的重点）

模型生成的东西不可信，所以执行前必须过闸：

- 只允许单条语句，必须 `SELECT` / `WITH` 开头
- 禁用关键字：`INSERT / UPDATE / DELETE / DROP / ALTER / CREATE / GRANT ...`
- 表名白名单：只允许 `users / products / orders`
- 没写 `LIMIT` 就自动补 `LIMIT 100`
- 校验不通过时直接返回错误给页面，不执行

更硬的一道防线（可选，工程上推荐）：给程序一个只读数据库账号

```sql
CREATE USER 'practice_ro'@'localhost' IDENTIFIED BY '...';
GRANT SELECT ON practice.* TO 'practice_ro'@'localhost';
```

### 接口

| 路径 | 方法 | 作用 |
|---|---|---|
| `/` | GET | 首页：输入中文问题；带 `?q=` 时走完整问答链路 |
| `/top-user` | GET | 返回 JSON：花钱最多的用户（v1 的固定查询，保留作对照） |
| `/echo` | GET | 调试用：回显 URL 参数，验证 `request.args` |
| `/demo-json` | GET | 教学用：演示 `jsonify` 与 Content-Type |
| `/ping` | GET | 健康检查，返回 pong |
| `/about` | GET | 个人介绍页 |
| `/static/style.css` | GET | 样式表（Flask 自动挂载） |

### 数据库

MySQL 8 的 `practice` 库（users 12 / products 8 / orders 40）。

- 账号密码在 `SQL/dbconfig.py`，已被 `.gitignore` 排除，**不会进仓库**；clone 下来要自己填。
- 业务口径：「花了多少钱」默认只统计 `status='paid'` 的订单；这个口径写在模型的提示词里。

### 自检

```bash
# 数据层 + 安全闸（不调模型，不花钱）
.venv\Scripts\python.exe Agent\db.py

# 完整问答链路（会调 2 次模型，花几毫钱）
.venv\Scripts\python.exe Agent\qa.py

# 页面结构 + 路由（启动服务时会自动跑，不调模型）
.venv\Scripts\python.exe Agent\app.py
```

### 版本路线

| 版本 | 状态 | 内容 |
|---|---|---|
| v1 | ✅ 已完成 | Flask + MySQL，固定查询，页面展示 |
| v2 | ✅ 已完成 | 接 LLM：中文问题 → SQL → 安全检查 → 执行 → 人话解释 |
| v3 | 计划中 | 工具调用结构 + 多轮记忆，支持连续追问 |

v1 里程碑：Hello world → 数据层 `db.py` → `/top-user` JSON → templates 表单页 → 前后端打通 + 样式 + README
v2 里程碑：接入 DeepSeek 生成 SQL → 只读安全闸 → 问答编排层 `qa.py` → 页面展示 SQL/表格/解释
