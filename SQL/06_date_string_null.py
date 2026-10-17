# ============================================================
# SQL 06：日期、字符串与 NULL —— 真实数据的三类毛刺
# 用法：右键 -> Run '06_date_string_null'
# 数据库：practice.db（同目录）
#
# 【本课三件事】
#   ① 日期：我们库里的日期其实是【文本】，怎么提取、计算、过滤
#   ② 字符串：清洗、拼接、模糊匹配
#   ③ NULL：本课重点 —— 它一直在坑你，这次把它一次说清
#
# 【面试频率 ★★★★】
#   「按月统计」「算时间间隔」「找出城市为空的用户」都是日常题。
#
# 【本课新词】
#   strftime / julianday / LIKE / SUBSTR / REPLACE / TRIM
#   字符串拼接 || / COALESCE / 三值逻辑
# ============================================================

import sqlite3
from pathlib import Path

DB = Path(__file__).with_name("practice.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()


# ------------------------------------------------------------
# 第一部分：热身（不用改，直接运行）
# ------------------------------------------------------------

# --- 1. 先看清：日期在我们库里其实是「文本」---
print("=== 1. 日期在本库里是 TEXT，不是日期类型 ===")
for cid, name, typ, notnull, dflt, pk in cur.execute("PRAGMA table_info(orders)").fetchall():
    if "date" in name:
        print(f"   {name:<12} 类型 = {typ}")
print("   -> SQLite 没有真正的日期类型，日期就是字符串 'YYYY-MM-DD'。")
print("      MySQL 那边有 DATE / DATETIME 类型，这是两者的重要差别。")
print("      ⚠️ 既然是字符串，格式就必须统一：'2024-1-5' 和 '2024-01-05'")
print("         排序和比较的结果会完全错乱 —— 这是脏数据里最常见的一种。")
print()

# --- 2. 从文本里提取部分（月度分组，实战第一课）---
print("=== 2. strftime：从日期里抠出年月 ===")
sample = cur.execute(
    "SELECT order_date, strftime('%Y', order_date), strftime('%m', order_date), strftime('%Y-%m', order_date) FROM orders LIMIT 3"
).fetchall()
for d, y, m, ym in sample:
    print(f"   {d}  ->  年 {y}  月 {m}  年月 {ym}")
print("   -> MySQL 对照：DATE_FORMAT(order_date, '%Y-%m')")
print()

print("=== 3. 按月统计订单数和金额（月度报表就是这么来的）===")
month = cur.execute(
    """
    SELECT strftime('%Y-%m', order_date) AS ym, COUNT(*), SUM(amount)
    FROM orders
    GROUP BY ym
    ORDER BY ym
    """
).fetchall()
for ym, n, total in month:
    print(f"   {ym}   {n:>3} 笔   {total:>9.1f} 元")
print()

# --- 4. 日期范围过滤：BETWEEN 的端点坑 ---
print("=== 4. BETWEEN 过滤日期，以及它的坑 ===")
q3 = cur.execute(
    "SELECT COUNT(*), SUM(amount) FROM orders WHERE order_date BETWEEN '2024-07-01' AND '2024-09-30'"
).fetchone()
print(f"   2024-07-01 ~ 2024-09-30：{q3[0]} 笔，{q3[1]} 元")
print("   -> BETWEEN 是「闭区间」，两端都包含。")
print("   ⚠️ 坑：如果这列是带时分秒的 DATETIME，写 ... AND '2024-09-30'")
print("      只能覆盖到 9-30 00:00:00，当天白天的数据全被漏掉，而且不报错。")
print("      安全写法：order_date >= '2024-07-01' AND order_date < '2024-10-01'")
print("      （用「小于下一个区间的开头」，而不是「小于等于本区间末尾」）")
print()

# --- 5. 日期计算 ---
print("=== 5. 日期相减算间隔、日期加减算偏移 ===")
days = cur.execute(
    """
    SELECT order_id, order_date,
           CAST(julianday('2024-12-31') - julianday(order_date) AS INTEGER)
    FROM orders ORDER BY order_id LIMIT 3
    """
).fetchall()
for oid, d, n in days:
    print(f"   订单{oid}  {d}  距 2024-12-31 还有 {n} 天")
print("   -> julianday() 把日期变成「第几天」，相减就是天数差。")
print("      日期加减：date('2024-09-30', '+7 day') =", cur.execute("SELECT date('2024-09-30', '+7 day')").fetchone()[0])
print("      MySQL 对照：DATEDIFF(a, b) 求天数差；DATE_ADD(d, INTERVAL 7 DAY) 做偏移。")
print()

# --- 6. 字符串函数速查 ---
print("=== 6. 字符串函数一小把 ===")
demo = cur.execute(
    """
    SELECT '  Hello SQL  ',
           TRIM('  Hello SQL  '),
           UPPER('abc'), LOWER('ABC'),
           LENGTH('abc'), SUBSTR('2024-09-08', 1, 4),
           REPLACE('2024-09-08', '-', '/'),
           '2024' || '年' || '09' || '月'
    """
).fetchone()
print("   TRIM 去空格：", repr(demo[0]), "->", repr(demo[1]))
print("   UPPER/LOWER：", demo[2], demo[3])
print("   LENGTH/SUBSTR：", demo[4], demo[5])
print("   REPLACE：", demo[6])
print("   拼接（用 ||）：", demo[7])
print("   -> 拼接在 MySQL 里要写 CONCAT(a, b, c)；SQLite 用 ||（标准 SQL 也是 ||）。")
print()

# --- 7. LIKE 模糊匹配 ---
print("=== 7. LIKE：% 表示任意多个字符，_ 表示一个字符 ===")
like1 = cur.execute("SELECT DISTINCT city FROM users WHERE city LIKE '%州'").fetchall()
like2 = cur.execute("SELECT DISTINCT city FROM users WHERE city LIKE '北_'").fetchall()
print("   LIKE '%州' ->", like1, "（结尾是州）")
print("   LIKE '北_' ->", like2, "（北 + 恰好一个字）")
print("   -> ⚠️ 前后都带 % （比如 '%州%'）时，索引基本用不上，大表上会变慢。")
print()

# --- 8. NULL 铁律①：!= 和 NOT IN 都会漏掉 NULL 行 ---
print("=== 8. NULL 铁律①：<> 和 != 会静默漏掉 NULL 行 ===")
a = cur.execute("SELECT COUNT(*) FROM users WHERE city != '北京'").fetchone()[0]
b = cur.execute("SELECT COUNT(*) FROM users WHERE city IS NULL OR city != '北京'").fetchone()[0]
total = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
bj = cur.execute("SELECT COUNT(*) FROM users WHERE city = '北京'").fetchone()[0]
print(f"   总人数 {total}，其中北京 {bj} 人")
print(f"   city != '北京'              -> {a} 人  ← 少了 1 个")
print(f"   city IS NULL OR city != ... -> {b} 人  ← 正确")
print("   -> 少的那个是周杰（city 是 NULL）：NULL != '北京' 的结果不是真，是「未知」，")
print("      所以他不满足条件，也不满足反条件 —— 从两个方向查他都不出现。")
print("      这跟 04 课 NOT IN 的坑是同一个根：**NULL 参与比较，结果是 UNKNOWN。**")
print()

# --- 9. NULL 铁律②：拼接时 NULL 会传染 ---
print("=== 9. NULL 铁律②：拼接遇到 NULL，整串变 NULL ===")
raw = cur.execute("SELECT '城市：' || city FROM users WHERE user_id = 8").fetchone()[0]
safe = cur.execute("SELECT '城市：' || COALESCE(city, '未填写') FROM users WHERE user_id = 8").fetchone()[0]
print("   '城市：' || city                        ->", repr(raw))
print("   '城市：' || COALESCE(city, '未填写')     ->", repr(safe))
print("   -> 一个 NULL 能把整条拼接结果变成 NULL。写报表、拼字符串时必备 COALESCE。")
print("      MySQL 里 COALESCE 也有，另外还有 IFNULL(a, b)。")
print()

# --- 10. NULL 不是「空字符串」，也不是 0 ---
print("=== 10. NULL 的语义：不是 0，不是空串，是「不知道」 ===")
demo2 = cur.execute(
    "SELECT NULL = NULL, NULL != NULL, LENGTH(NULL), COALESCE(NULL, 0), COALESCE('', 0)"
).fetchone()
print("   NULL = NULL   ->", demo2[0], "（连自己都不等于自己）")
print("   NULL != NULL  ->", demo2[1])
print("   LENGTH(NULL)  ->", demo2[2])
print("   COALESCE(NULL, 0) ->", demo2[3], "  COALESCE('', 0) ->", demo2[4], "（空串不是 NULL）")
print("   -> 判断 NULL 只能用 IS NULL / IS NOT NULL，不能用 = NULL。")
print()


# ------------------------------------------------------------
# 第二部分：过关任务（在这里作答）
# ------------------------------------------------------------
# 说明：为方便自检区显示，凡是要求「前 5 条」的，都在 SQL 里写 LIMIT 5。
#      想看全部数据，把 LIMIT 5 去掉自己再跑一次。

# TODO 1：按月统计订单数和总金额
#         输出三列：月份（形如 2024-07）、订单数、总金额；按月份升序
#         结果存给 rows_month（共 6 行）
rows_month = cur.execute(
    """SELECT strftime('%Y-%m', order_date), COUNT(*), SUM(amount)
    FROM orders
    GROUP BY strftime('%m', order_date)
    ORDER BY strftime('%m', order_date)""").fetchall()

# TODO 2：2024 年 7 月到 9 月的订单数和总金额
#         要求：用日期比较，不许用 LIKE 字符串匹配
#         两个数分别存给 q3_count、q3_sum
q3_count = cur.execute(
    """SELECT COUNT(*)
    FROM orders
    WHERE strftime('%m', order_date) >= '07' AND strftime('%m', order_date) <= '09'
    """).fetchone()[0]
q3_sum = cur.execute(
    """SELECT SUM(amount)
    FROM orders
    WHERE strftime('%m', order_date) >= '07' AND strftime('%m', order_date) <= '09'
    """).fetchone()[0]

# TODO 3：每笔订单距离 '2024-12-31' 有多少天
#         输出 order_id、order_date、天数；按 order_id 升序，取前 5 条
#         结果存给 rows_days
rows_days = cur.execute(
    """SELECT order_id, order_date, CAST(julianday('2024-12-31') - julianday(order_date) AS days)
    FROM orders
    ORDER BY order_id
    LIMIT 5""").fetchall()

# TODO 4：做出形如「2024年07月」的月份标签，并统计该月订单数
#         输出两列：标签、订单数；按标签升序
#         结果存给 rows_label（用字符串拼接，别在 Python 里拼）
rows_label = cur.execute(
    """SELECT strftime('%Y年%m月', order_date), COUNT(*)
    FROM orders
    GROUP BY strftime('%m', order_date)""").fetchall()

# TODO 5：NULL 陷阱（本课重点）
#         - n_wrong：用 city != '北京' 数出的「非北京用户」人数
#         - n_right：修正后的人数
#         写完后在注释里回答：少了谁？为什么会少？
n_wrong = cur.execute(
    """SELECT COUNT(*)
    FROM users
    WHERE city != '北京'""").fetchone()[0]
n_right = cur.execute(
    """SELECT COUNT(*)
    FROM users
    WHERE city IS NULL OR city != '北京'"""
).fetchone()[0]
# 你的解释：NULL会被忽略，无论是否满足要求

# TODO 6（不写代码，写在注释里）：
#         如果 order_date 是带时分秒的 DATETIME 类型，
#         WHERE order_date BETWEEN '2024-07-01' AND '2024-09-30' 会漏掉什么数据？怎么改？
# 你的答案：会漏掉9月30号当日的数据，改成2024-10-1


# ------------------------------------------------------------
# 第三部分：自检区（不要改）
# ------------------------------------------------------------
print("===== 自检 =====")
print("TODO1 rows_month ->", rows_month)
print("      | 期望 [('2024-07',8,2656.0), ('2024-08',6,3441.0), ('2024-09',13,6929.0), ('2024-10',1,1497.0), ('2024-11',4,2753.0), ('2024-12',8,2348.0)]")
print()
print("TODO2 q3_count ->", q3_count, "| 期望 27")
print("TODO2 q3_sum   ->", q3_sum, "| 期望 13026.0")
print()
print("TODO3 rows_days ->", rows_days)
print("      | 期望 [(1,'2024-09-08',114), (2,'2024-12-18',13), (3,'2024-07-03',181), (4,'2024-08-23',130), (5,'2024-10-19',73)]")
print()
print("TODO4 rows_label ->", rows_label)
print("      | 期望 [('2024年07月',8), ('2024年08月',6), ('2024年09月',13), ('2024年10月',1), ('2024年11月',4), ('2024年12月',8)]")
print()
print("TODO5 n_wrong ->", n_wrong, "| 期望 7（少了一个人）")
print("TODO5 n_right ->", n_right, "| 期望 8")
print()
print("全对的话，日期、字符串、NULL 这三类毛刺你都能处理了。")
print("下一课 07：面试真题综合（把 01-06 全部用上）。")
