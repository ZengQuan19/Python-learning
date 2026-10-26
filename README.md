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

**当前进度：v1 已完成** ✅（Flask + MySQL，输入中文问题 → 页面显示查询结果，不含 AI）

### 目录结构

```
Agent/
├─ app.py            # 入口：路由 + 页面 + 自检
├─ db.py             # 数据层：连库 + 查询函数
├─ templates/
│  └─ index.html     # 首页模板（输入框 + 结果区）
└─ static/
   └─ style.css      # 样式表
```

### 运行

```bash
# 1. 装依赖（只需一次）
.venv\Scripts\python.exe -m pip install flask pymysql

# 2. 启动服务
.venv\Scripts\python.exe Agent\app.py
```

浏览器打开 http://127.0.0.1:5000 ，输入「哪个用户花钱最多」并提交。

启动时会在终端打印四组自检（路由表、JSON 接口、模板渲染、端到端流程），全部通过再开浏览器。

### 接口

| 路径 | 方法 | 作用 |
|---|---|---|
| `/` | GET | 首页：输入问题；带 `?q=` 时显示查询结果 |
| `/top-user` | GET | 返回 JSON：花钱最多的用户 |
| `/echo` | GET | 调试用：回显 URL 参数，验证 `request.args` |
| `/demo-json` | GET | 教学用：演示 `jsonify` 与 Content-Type |
| `/ping` | GET | 健康检查，返回 pong |
| `/about` | GET | 个人介绍页 |
| `/static/style.css` | GET | 样式表（Flask 自动挂载） |

### 数据库

MySQL 8 的 `practice` 库（users 12 / products 8 / orders 40）。

- 账号密码在 `SQL/dbconfig.py`，已被 `.gitignore` 排除，**不会进仓库**；clone 下来要自己填。
- 只允许 `SELECT`，所有条件用 `%s` 占位符传参，不拼字符串。
- 「花钱最多」的口径：只统计 `status='paid'` 的订单。

### 单独跑数据层自检

```bash
.venv\Scripts\python.exe Agent\db.py
```

### 版本路线

| 版本 | 状态 | 内容 |
|---|---|---|
| v1 | ✅ 已完成 | Flask + MySQL，固定查询，页面展示 |
| v2 | 计划中 | 接 LLM：中文问题 → SQL → 执行 → 人话解释 |
| v3 | 计划中 | 工具调用结构 + 多轮记忆，支持连续追问 |

v1 里程碑：Hello world ✅ → 数据层 `db.py` ✅ → `/top-user` JSON ✅ → templates 表单页 ✅ → 前后端打通 + 样式 + README ✅
