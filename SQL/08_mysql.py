# ============================================================
# SQL 08：把练习搬到 MySQL —— 建库、灌数据、跑查询
# 用法：右键 -> Run '08_mysql'
#
# 【前提】
#   1. MySQL80 服务在运行
#   2. 同目录的 dbconfig.py 里填好了账号密码（这个文件不会进 git）
#
# ============================================================
# 【先回答那个疑问：MySQL 和 SQLite 到底差多少？】
#
#   好消息：占你 95% 学习内容的【核心语法，完全一样】——
#     SELECT / FROM / WHERE / GROUP BY / HAVING / ORDER BY / LIMIT
#     JOIN / ON / INNER / LEFT / CASE WHEN / IN / NOT IN / EXISTS
#     OVER / PARTITION BY / ROW_NUMBER / RANK / DENSE_RANK / LAG
#     COALESCE / IS NULL
#   你在 01–07 学过的这些东西，一个字都不用改，直接搬到 MySQL 就能跑。
#   所以你不是"要重新学一门 SQL"。
#
#   真正不同的只是【外围零件】，分四类：
#     ① Python 驱动层：占位符 ?  →  %s            ← 跟数据库无关，是驱动的事
#     ② 函数名不同：日期、字符串                      ← 记不住就查，不影响理解
#     ③ 默认行为不同：整数除法、GROUP BY 严格模式      ← 要记！会静默出错
#     ④ 数据库特有：看结构用 DESC/SHOW、建表要写长度/类型
#
#   本课就是把这四类逐个过一遍。
# ============================================================

import sqlite3
from pathlib import Path

import pymysql

from dbconfig import CHARSET, HOST, PASSWORD, PORT, USER

HERE = Path(__file__).parent      # 本文件所在的目录（SQL\）
DB_NAME = "practice"              # 我们要建的库名


# ------------------------------------------------------------
# 第 0 步：连接 MySQL
# ------------------------------------------------------------
print("=== 0. 连接 MySQL ===")
# sqlite3 的连接是「打开一个文件」，pymysql 的连接是「通过网络连一个服务」，
# 所以参数完全不同：要主机、端口、用户名、密码。
try:
    conn = pymysql.connect(
        host=HOST,              # 数据库在哪台机器（本机就是 localhost）
        port=PORT,              # 端口，MySQL 默认 3306
        user=USER,              # 账号
        password=PASSWORD,      # 密码
        charset=CHARSET,        # 字符集。utf8mb4 = 完整 UTF-8（能存中文、emoji）
        autocommit=True,        # 每条语句立刻生效，不用手动 commit
        #                         （SQLite 也是自动提交；MySQL 默认要手动 commit，
        #                           这里设成 True 是为了和 SQLite 的手感一致）
    )
except pymysql.err.OperationalError as e:
    # 连不上时报的是 OperationalError，不是"用户名密码错"这么具体。
    # 三个最常见原因，按可能性排序：
    print("   连不上，错误是：", e)
    print("   ① MySQL80 服务没启动（PowerShell: Get-Service MySQL80）")
    print("   ② dbconfig.py 里的账号/密码不对")
    print("   ③ 端口不是 3306（装的时候改过？）")
    raise SystemExit(1)          # 退出程序，不往下跑了

cur = conn.cursor()              # 和 sqlite3 一样：先拿游标，再用游标执行
cur.execute("SELECT VERSION(), CURRENT_USER(), @@character_set_server")
ver, who, cs = cur.fetchone()    # fetchone 拿一行，再解包成三个变量
print(f"   版本：{ver}")
print(f"   当前用户：{who}")
print(f"   服务端默认字符集：{cs}")
print("   -> 这三行是「问候语」：确认连上了、连的是谁、字符集对不对")
print()


# ------------------------------------------------------------
# 第 1 步：建库
# ------------------------------------------------------------
print("=== 1. 建库 ===")
# SQLite 里「一个文件就是一个库」，没有 CREATE DATABASE 这回事。
# MySQL 是一台服务器上可以有很多库（schema），所以要先建库。
#
# IF NOT EXISTS 很关键：重复运行这段代码时不会报"库已存在"。
# 这种「跑几次结果都一样」的写法叫【幂等】，是写脚本的好习惯。
cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET utf8mb4")
print(f"   {DB_NAME} 库已就绪")

# USE = 切换到某个库。之后所有表操作都在这个库里。
# 相当于 Python 里的 `os.chdir()`：切工作目录。
cur.execute(f"USE {DB_NAME}")
print("   已切换到这个库（USE 相当于 Python 里切工作目录）")
print()


# ------------------------------------------------------------
# 第 2 步：建表（DDL = 定义结构的语句）
# ------------------------------------------------------------
print("=== 2. 建表 ===")
# ⚠️ DROP 会删表！这里敢用，只因为 practice 是你的练习库。
#    真实工作里，绝不对生产库写 DROP TABLE —— 这是能让人丢工作的操作。
#
# 为什么要先 DROP？因为表可能已经存在（上次跑过）。
# 先删再建 = 每次运行都是干净的一套数据，这也是"幂等"。
cur.execute("DROP TABLE IF EXISTS orders")     # 先删子表（理论上没关系，习惯从依赖末端删）
cur.execute("DROP TABLE IF EXISTS products")
cur.execute("DROP TABLE IF EXISTS users")

# 建表时和 SQLite 的三个关键差异：
#   ① 文字列必须写长度：VARCHAR(50) —— SQLite 写 TEXT 就行，长度随便。
#      MySQL 要预留空间：50 = 最多 50 个字符。
#   ② 有真正的数据类型：DATE（日期）、DECIMAL（精确小数）、INT（整数）。
#      SQLite 是"动态类型"，什么都能往里塞，不检查。
#   ③ 金额用 DECIMAL(10,2) 而不是 FLOAT：
#      FLOAT 是二进制浮点，会有 0.1+0.2 != 0.3 那种误差；
#      DECIMAL 是精确十进制，专门给钱用。真实项目里金额一律 DECIMAL。
#
# 另外：MySQL 里表名/列名要加引号时用【反引号】 `名字`
#       （因为标准双引号 "名字" 在 MySQL 默认被当成字符串）
cur.execute(
    """
    CREATE TABLE users (
        user_id     INT PRIMARY KEY,             -- 主键：唯一、不能重复
        name        VARCHAR(50) NOT NULL,        -- NOT NULL：这一列不许空
        city        VARCHAR(20),                 -- 没写 NOT NULL = 允许 NULL
        signup_date DATE,                        -- 真正的日期类型
        age         INT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4      -- InnoDB=支持事务和行锁的引擎
    """
)
cur.execute(
    """
    CREATE TABLE products (
        product_id   INT PRIMARY KEY,
        product_name VARCHAR(50) NOT NULL,
        price        DECIMAL(10, 2),             -- 总共 10 位，其中 2 位小数
        category     VARCHAR(20)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """
)
cur.execute(
    """
    CREATE TABLE orders (
        order_id   INT PRIMARY KEY,
        user_id    INT,
        product_id INT,
        quantity   INT,
        amount     DECIMAL(10, 2),
        status     VARCHAR(20),
        order_date DATE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """
)
print("   users / products / orders 三张表已建好")
print()


# ------------------------------------------------------------
# 第 3 步：看表结构
# ------------------------------------------------------------
print("=== 3. 看表结构：DESC orders（对应 SQLite 的 PRAGMA table_info）===")
# SQLite: PRAGMA table_info(orders)  → 每行 6 个字段
# MySQL : DESC orders                → 列更少但更直观
cur.execute("DESC orders")
for row in cur.fetchall():
    print("   ", row)
# 输出的每一行是：Field(列名) / Type(类型) / Null(是否允许空) /
#                Key(是不是主键) / Default(默认值) / Extra(额外信息，如自增)
print("   读法：第一列是列名，第二列是类型，第三列 YES 表示允许 NULL")
print()


# ------------------------------------------------------------
# 第 4 步：把 SQLite 的数据搬过来（读取 → 写入）
# ------------------------------------------------------------
print("=== 4. 从 practice.db 搬数据到 MySQL ===")
# 这一步是最朴素的 ETL：
#   E(xtract) 从 SQLite 读出来 → T(ransform) 这里没做转换 → L(oad) 写进 MySQL
src = sqlite3.connect(HERE / "practice.db")

for table, cols in [
    ("users", 5),        # 表名, 这张表有几列
    ("products", 4),
    ("orders", 7),
]:
    # ① 从 SQLite 读出全部行。fetchall() 得到的是 [(...), (...), ...]
    rows = src.execute(f"SELECT * FROM {table}").fetchall()

    # ② 造占位符字符串，比如 5 列 → "%s, %s, %s, %s, %s"
    #    【差异①】pymysql 的占位符是 %s，sqlite3 是 ?
    #    注意：这里的 %s 不是 Python 的 % 格式化！是 pymysql 自己的占位符语法，
    #         所以 SQL 里有 % 也要小心（好在我们的 SQL 没有）。
    placeholders = ", ".join(["%s"] * cols)

    # ③ executemany = 一次把一批数据交给驱动，比 for 循环逐条 execute 快得多
    cur.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
    print(f"   {table:<9} 搬过来 {len(rows)} 行")

src.close()
print("   -> 注意：SQLite 里 signup_date 存的是文本 '2024-01-05'，")
print("      插进 MySQL 的 DATE 类型列时，MySQL 会自动把它解析成日期，不用手动转换。")
print()


# ------------------------------------------------------------
# 第 5 步：验收 —— 源和目标的条数必须一致
# ------------------------------------------------------------
print("=== 5. 验证行数（应该和 SQLite 完全一致：12 / 8 / 40）===")
# 这是数据迁移的第一条铁律：**搬完之后对比条数**。
# 少了说明有行被拒绝（类型不符/主键冲突），多了说明重复插入了。
for t in ("users", "products", "orders"):
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"   {t:<9} {cur.fetchone()[0]} 行")
print()


# ------------------------------------------------------------
# 第 6 步：同一个查询，两个数据库各跑一遍
# ------------------------------------------------------------
print("=== 6. 对照：月度 GMV（有效订单口径）===")
# 【差异②】日期函数：同样是"取出 年-月"
#    SQLite: strftime('%Y-%m', order_date)
#    MySQL : DATE_FORMAT(order_date, '%Y-%m')
# 除了这个函数名，其余（WHERE / GROUP BY / ORDER BY）一模一样。
cur.execute(
    """
    SELECT DATE_FORMAT(order_date, '%Y-%m') AS ym,
           COUNT(*), SUM(amount)
    FROM orders
    WHERE status IN ('paid', 'pending')
    GROUP BY ym
    ORDER BY ym
    """
)
print("   MySQL：")
for r in cur.fetchall():
    print("     ", r)

src2 = sqlite3.connect(HERE / "practice.db")
print("   SQLite：")
for r in src2.execute(
    """
    SELECT strftime('%Y-%m', order_date), COUNT(*), SUM(amount)
    FROM orders WHERE status IN ('paid', 'pending')
    GROUP BY 1 ORDER BY 1
    """
).fetchall():
    print("     ", r)
src2.close()
print("   -> 两边必须一模一样。不一样说明数据没搬全，或者口径写差了。")
print("   -> 注意金额显示：MySQL 的 DECIMAL 返回的是 Decimal('1681.00')，")
print("      带两位小数；SQLite 返回 float 1681.0。数值相等，只是类型不同。")
print()


# ------------------------------------------------------------
# 第 7 步：四个必须记住的差异
# ------------------------------------------------------------
print("=== 7. SQLite 和 MySQL 的差异 ===")

# ---------- 差异①：占位符 ----------
print("① 占位符：SQLite 用 ? ，pymysql 用 %s")
# 这其实不是数据库的差异，是【Python 驱动】的差异：
#   sqlite3 模块规定用 ? ；pymysql 规定用 %s 。
# 传参数用元组，pymysql 会自动做转义，防止 SQL 注入。
cur.execute("SELECT name FROM users WHERE age > %s", (30,))
print("   MySQL: WHERE age > %s  ->", [r[0] for r in cur.fetchall()][:3], "...")
print()

# ---------- 差异②：字符串拼接 ----------
print("② 字符串拼接：SQLite 用 || ，MySQL 必须用 CONCAT()")
cur.execute("SELECT CONCAT('2024', '年', '07', '月')")
print("   CONCAT('2024','年','07','月') ->", cur.fetchone()[0])
cur.execute("SELECT '2024' || '07'")
print("   而 '2024' || '07' ->", cur.fetchone()[0], "  ← MySQL 里 || 是【逻辑或】，不是拼接！")
cur.execute("SELECT @@sql_mode")
print("   当前 sql_mode:", cur.fetchone()[0])
print("   -> 为什么是 1？因为 '2024' 当布尔值是 TRUE，两个 TRUE「或」起来还是 TRUE，")
print("      而 MySQL 的 TRUE 用数字 1 表示。所以拼接的意图，被悄悄变成了真假判断。")
print("      这不是 bug，是历史包袱（SQL 标准里 || 本来是拼接）。")
print("      ⚠️ 它【不报错】，只是悄悄给你一个 1 —— 又一个静默失败。")
print("      对照：同样一句在 SQLite 里会得到 '202407'。")
print("      所以在 MySQL 里拼字符串，永远写 CONCAT。")
print()

# ---------- 差异③：整数除法 ----------
print("③ 整数除法：方向相反")
cur.execute("SELECT 100 / 40")
print("   MySQL 的 100 / 40 =", cur.fetchone()[0], "  ← 直接给小数")
print("   （SQLite 里 100/40 = 2，因为整数除法会截断 —— 你在 04 课踩过那个 0.5 的坑）")
cur.execute("SELECT 100 DIV 40")
print("   MySQL 要整除得写 DIV：100 DIV 40 =", cur.fetchone()[0])
print("   -> 所以：SQLite 想要小数要写 100.0，MySQL 想要整数要写 DIV。")
print("      两边默认行为相反，这是最容易在跨库时算错的地方。")
print()

# ---------- 差异④：GROUP BY 严格模式 ----------
print("④ GROUP BY 严格模式：MySQL 默认不许裸列")
# 「裸列」= SELECT 里出现、但既没分组也没聚合的列。
# 你在 02、03 课见过：SQLite 会随便挑一个值给你，不报错。
# MySQL 8 默认开启 ONLY_FULL_GROUP_BY，会直接拒绝这种写法。
try:
    cur.execute("SELECT status, order_id, COUNT(*) FROM orders GROUP BY status")
    print("   居然没报错？", cur.fetchall())
except pymysql.err.OperationalError as e:
    print("   报错：", e)
    print("   -> 这不是 MySQL 不友好，是它【帮你抓错】。")
    print("      你在 SQLite 上写这种会被静默放行，结果看着像对的其实是随机的。")
print()

# ---------- 差异⑤：cur.execute() 的返回值不同（Python 驱动层，最坑的一个）----------
print("⑤ cur.execute() 返回什么？两个驱动不一样")
n_demo = cur.execute("SELECT 1")
print("   pymysql: cur.execute('SELECT 1') ->", n_demo, "（类型", type(n_demo).__name__, "，是行数）")
print("   -> 所以 rows = cur.execute(sql) 拿到的是【一个数字】，不是查询结果。")
print("      正确写法永远是两步：cur.execute(sql)  然后  rows = cur.fetchall()")
src4 = sqlite3.connect(HERE / "practice.db")
print("   sqlite3: execute(...) 返回的是游标本身，所以能链式写 .fetchall() ->",
      src4.execute("SELECT 1").fetchall())
src4.close()
print("   ⚠️ 同一个写法在两个驱动里含义不同 —— 这就是为什么你在 01–07 课里")
print("      一直能写 cur.execute(...).fetchall()，换到 MySQL 却只拿到一个数字。")
print()

# ---------- 差异⑥：fetchall() 返回的类型不同 ----------
print("⑥ fetchall() 返回的类型：sqlite3 给 list，pymysql 给 tuple")
cur.execute("SELECT 1 UNION SELECT 2")
print("   pymysql ->", type(cur.fetchall()).__name__)
src5 = sqlite3.connect(HERE / "practice.db")
print("   sqlite3 ->", type(src5.execute("SELECT 1 UNION SELECT 2").fetchall()).__name__)
src5.close()
print("   -> 影响：MySQL 上 rows.append(...) 会报错（tuple 不能 append）。")
print("      要改就写 rows = list(cur.fetchall())。")
print()

# ---------- 附：常用函数名对照（记不住就抄这张）----------
print("附：函数名对照表（SQLite -> MySQL）")
print("   取年月      strftime('%Y-%m', d)       -> DATE_FORMAT(d, '%Y-%m')")
print("   天数差      julianday(a)-julianday(b)  -> DATEDIFF(a, b)     <- 注意没有下划线！")
print("   当前时间    datetime('now')            -> NOW()")
print("   字符串拼接  a || b                     -> CONCAT(a, b)")
print("   整除        100/40 = 2（截断）          -> 100 DIV 40")
print()


# ------------------------------------------------------------
# 第二部分：过关任务（在这里作答）
# ------------------------------------------------------------

# TODO 1【连库】：写一个函数 get_conn()，返回一个连接好 practice 库的 pymysql 连接
#         要求：autocommit=True，字符集 utf8mb4，并且直接连到 practice 库（用 database 参数）
#         提示：pymysql.connect(database="practice", ...) 就是"连上并 USE"
def get_conn():
    conn = pymysql.connect(
        host = HOST,
        port = PORT,
        user = USER,
        password = PASSWORD,
        charset = CHARSET,
        autocommit = True,
        database = "practice"
    )
    return conn

# TODO 2【月度环比】：在 MySQL 上算出「有效订单的月度 GMV + 环比增长率」
#         输出：ym, gmv, 环比（百分比保留 1 位，第一行 NULL），按 ym 升序
#         结果存给 rows_mom_mysql
#         提示：你在 07 课写过 SQLite 版，这题只差日期函数（DATE_FORMAT）
cur.execute(
    """WITH t AS (SELECT DATE_FORMAT(order_date,'%Y-%m') AS ym, SUM(amount) AS gmv
    FROM orders
    WHERE status IN ('paid', 'pending')
    GROUP BY ym
    ORDER BY ym)
    SELECT ym, gmv , ROUND((gmv - LAG(gmv) OVER(ORDER BY ym)) * 100 / LAG(gmv) OVER(ORDER BY ym), 1)
    FROM t
    ORDER BY ym"""
)
rows_mom_mysql = cur.fetchall()

# TODO 3【经典题重做】：每个城市订单数最多的用户（Top1），订单数并列按 user_id 升序
#         输出：city, user_id, name, n，按 city 升序
#         结果存给 rows_city_top_mysql
#         提示：ROW_NUMBER() 在 MySQL 8 里用法和 SQLite 一样
cur.execute(
    """WITH t AS (SELECT u.city AS City, u.user_id, u.name, COUNT(o.order_id) AS n,
                ROW_NUMBER() OVER (PARTITION BY u.city ORDER BY COUNT(o.order_id) DESC, u.user_id) AS rn
    FROM users u
    LEFT JOIN orders o ON o.user_id = u.user_id
    GROUP BY u.user_id)
    SELECT City, user_id, name, n
    FROM t
    WHERE rn = 1
    ORDER BY City
    """
)
rows_city_top_mysql = cur.fetchall()

# TODO 4【NULL 陷阱复核】：在 MySQL 上验证 04 课那个坑
#         分别算出：city NOT IN ('北京','上海') 的人数、加上 IS NULL 后的正确人数
#         存给 n_wrong_mysql / n_right_mysql
#         预期：MySQL 的结果和 SQLite 一样（4 和 5）
cur.execute(
    """SELECT COUNT(*)
    FROM users
    WHERE city NOT IN ('北京', '上海')"""
)
n_wrong_mysql = cur.fetchone()[0]
cur.execute(
    """SELECT COUNT(*)
    FROM users
    WHERE city NOT IN ('北京', '上海') OR city IS NULL"""
)
n_right_mysql = cur.fetchone()[0]

# TODO 5（不写代码，写在注释里）：
#         用你自己的话写下 3 条「SQLite vs MySQL 差异」，每条一句话。
#         提示：从占位符、日期函数、字符串拼接、整数除法、GROUP BY 严格模式里挑
# 你的答案：占位符由? -> %s,字符串凭借得用CONCAT,日期函数是DATE_FORMAT且日期差用DATEDIFF,整数除法用DIV


# ------------------------------------------------------------
# 第三部分：自检区（不要改）
# ------------------------------------------------------------
print("===== 自检 =====")
c = get_conn()
print("TODO1 get_conn() ->", c, "| 期望是一个 <pymysql...Connection> 对象")
if c is not None:
    cc = c.cursor()
    cc.execute("SELECT DATABASE(), @@character_set_client")
    print("      连到了库 / 字符集 ->", cc.fetchone())
print()
print("TODO2 rows_mom_mysql ->", rows_mom_mysql)
print("      | 期望 [('2024-07', Decimal('1681.00'), None), ('2024-08', Decimal('3182.00'), 89.3), ...]")
print("      | 提示：MySQL 的 DECIMAL 会返回 Decimal 对象，不是 float，这很正常")
print()
print("TODO3 rows_city_top_mysql ->", rows_city_top_mysql)
print("      | 期望 6 行，按城市升序，NULL 城市排最前（MySQL 里 NULL 也是排最前）")
print()
print("TODO4 n_wrong_mysql ->", n_wrong_mysql, "| 期望 4")
print("TODO4 n_right_mysql ->", n_right_mysql, "| 期望 5")
print()
print("全对的话，你就完成了「同一个 SQL，两种数据库」的迁移与对照。")
print("这正是面试里问「你用过 MySQL 吗」时，你能讲出来的东西。")
