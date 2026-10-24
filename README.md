# Python 学习练习

大一上学期（2026 秋）的学习记录，从零开始学 Python 数据分析与 SQL，最后做一个网页版《数据分析 Agent》。

## 内容

- `SQL/`：SQL 基础 01–07（SELECT、GROUP BY、JOIN、CASE、窗口函数、日期函数、面试真题）
- `Net/`：第一次 HTTP 请求
- `Agent/`：《数据分析 Agent》网页工程（v1 Flask+MySQL → v2 接 LLM → v3 工具调用+多轮记忆）
- `*.py`：早期 NumPy / pandas / sklearn 练习

## 怎么跑

需要 Python 3.13 + pandas + scikit-learn。

```bash
python SQL/01_select.py
```

## Agent/：数据分析 Agent

当前进度：**v1 第 1 步（Flask 跑通）+ 第 2 步（数据层，进行中）**

依赖：Flask 3.1、pymysql（已装在项目 `.venv` 里）

```bash
.venv\Scripts\python.exe -m pip install flask pymysql
.venv\Scripts\python.exe Agent\app.py
```

浏览器打开 http://127.0.0.1:5000

| 路径 | 作用 |
|---|---|
| `/` | 首页，返回一句话 |
| `/ping` | 健康检查，返回 pong |
| `/about` | 个人介绍页（HTML） |

单独跑数据层自检（不用开 Flask）：

```bash
.venv\Scripts\python.exe Agent\db.py
```

数据库：MySQL 8 的 `practice` 库（users 12 / products 8 / orders 40）。
账号密码在 `SQL/dbconfig.py`，已被 `.gitignore` 排除，**不会进仓库**；clone 下来要自己填。

v1 路线：Flask Hello world ✅ → 数据层 `db.py` → `/top-user` 返回 JSON → 输入框页面 → 组装成完整 v1。
