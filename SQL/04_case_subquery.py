# ============================================================
# SQL 04：CASE WHEN + 子查询 —— 把条件写进查询里面
# 用法：右键 -> Run '04_case_subquery'
# 数据库：practice.db（同目录）
#
# 【本课两件事】
#   ① CASE WHEN：在查询里写 if-else。用来分箱、打标签、自定义排序
#   ② 子查询：查询里面再套一个查询。用来当"一个数"、当"一张临时表"、当条件
#
# 【面试频率 ★★★★★】
#   「把金额分档统计」「各状态占比」「找出没有下过单的用户」—— 全是这一类。
#
# 【本课新词】
#   分箱 / 标量子查询 / 派生表 / IN / NOT IN / EXISTS
#   ⚠️ 以及本课最重要的：NULL 遇到 NOT IN 会静默失效
# ============================================================

import sqlite3
from pathlib import Path

DB = Path(__file__).with_name("practice.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()


# ------------------------------------------------------------
# 第一部分：热身（不用改，直接运行）
# ------------------------------------------------------------

# --- 1. CASE WHEN：在查询里写 if-else ---
print("=== 1. CASE WHEN：给每笔订单打个标签 ===")
rows = cur.execute(
    """
    SELECT order_id, amount,
           CASE WHEN amount < 200  THEN '小额'
                WHEN amount < 1000 THEN '中额'
                ELSE '大额'
           END AS 档位
    FROM orders
    ORDER BY order_id
    LIMIT 5
    """
).fetchall()
for r in rows:
    print("   ", r)
print("   -> 语法：CASE WHEN 条件 THEN 值  WHEN 条件 THEN 值  ELSE 兜底 END")
print("      它是在 [查出来的结果里] 造一列新数据，不改数据库里的任何东西。")
print()
# ⚠️ 写 CASE 时的四个高频错误（都在这一课踩过）：
#   ① CASE 表达式如果出现在已有列后面，前面那个逗号别忘：
#        SELECT COUNT(*), SUM(amount), CASE ... END   <- SUM 后面必须有逗号
#      报错会显示 near "CASE": syntax error —— 报错点就是"断点"。
#   ② ELSE 后面不接 THEN：写 ELSE '大额'，不是 ELSE THEN '大额'
#   ③ 别在 SELECT 里再手写一个 '档位' 占位 —— CASE ... END AS 档位 自己就是这一列
#   ④ 【引号规则，最容易静默出错】
#        单引号 '档位'  = 字符串常量    -> GROUP BY '档位' 会把所有行并成 1 组！
#        不加引号 档位  = 标识符（列名/别名）<- 正确用法
#        中文弯引号 ‘档位’ = 一个奇怪标识符 -> no such column
#        双引号 "档位"  = 标识符，但 SQLite 找不到同名列时会退化成字符串（不可靠）
#      口诀：文字值用单引号，列名/别名不加引号。
print()

# --- 2. CASE + GROUP BY：分箱统计（实战里最常见的形态）---
print("=== 2. 分箱统计：各档位有多少笔、多少钱 ===")
case_rows = cur.execute(
    """
    SELECT CASE WHEN amount < 200  THEN '小额'
                WHEN amount < 1000 THEN '中额'
                ELSE '大额'
           END AS 档位,
           COUNT(*), SUM(amount)
    FROM orders
    GROUP BY 档位
    ORDER BY MIN(amount)
    """
).fetchall()
for d, n, total in case_rows:
    print(f"   {d}  {n:>3} 笔  {total:>10.1f} 元")
print("   -> 先用 CASE 造出「档位」这一列，再按它 GROUP BY。")
print("      ORDER BY MIN(amount) 是一招：让档位按金额从低到高排，")
print("      而不是按汉字拼音/编码排（否则大额会排在第一个）。")
print()

# --- 3. 坑①：CASE 是「第一个满足就停」，顺序写错结果全变 ---
print("=== 3. 坑①：CASE 条件顺序敏感 ===")
bad_order = cur.execute(
    """
    SELECT CASE WHEN amount < 1000 THEN '中额'
                WHEN amount < 200  THEN '小额'
                ELSE '大额'
           END AS 档位, COUNT(*)
    FROM orders GROUP BY 档位 ORDER BY MIN(amount)
    """
).fetchall()
print("   ", bad_order)
print("   -> 小额那一档「消失」了（11 笔被并进了中额）。")
print("      因为 amount=89 也满足 <1000，CASE 碰到第一个满足的就停，")
print("      永远不会走到第二行。写 CASE 时：**严格的、范围小的条件放前面**。")
print()

# --- 4. 坑②：忘了 ELSE，会得到 NULL（不是 0、不是原值）---
print("=== 4. 坑②：忘了 ELSE 就是 NULL ===")
no_else = cur.execute(
    """
    SELECT status, CASE WHEN status = 'paid' THEN '已付' END AS 标签, COUNT(*)
    FROM orders GROUP BY status
    """
).fetchall()
print("   ", no_else)
print("   -> 没写 ELSE 的档位全是 None。后面如果拿它做统计，会安静地少算。")
print()

# --- 5. 标量子查询：子查询返回「一个数」，可以当数值用 ---
print("=== 5. 标量子查询：比平均金额更高的订单 ===")
avg = cur.execute("SELECT AVG(amount) FROM orders").fetchone()[0]
n_above = cur.execute(
    "SELECT COUNT(*) FROM orders WHERE amount > (SELECT AVG(amount) FROM orders)"
).fetchone()[0]
print(f"   全表平均 = {avg:.2f}，高于平均的订单有 {n_above} 笔")
print("   -> 括号里那个 SELECT 先算出「一个数」，外层再拿它当条件用。")
print("      这叫标量子查询（scalar subquery）：它必须只返回一行一列。")
print()

# --- 6. 子查询当分母：算占比 ---
print("=== 6. 子查询做分母：各状态订单占比 ===")
pct = cur.execute(
    """
    SELECT status, COUNT(*),
           ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM orders), 1) AS pct
    FROM orders
    GROUP BY status
    ORDER BY pct DESC
    """
).fetchall()
for s, n, p in pct:
    print(f"   {s:<10}{n:>3} 笔   {p:>5}%")
print("   -> 分组统计里想算「占比」，分母往往是「全表总数」，")
print("      而全表总数正好用一个标量子查询拿到。")
print()

# --- 7. 重点坑③：NOT IN 遇到 NULL 会静默失效 ---
print("=== 7. 坑③：NOT IN 和 NULL（本节最重要）===")
a = cur.execute("SELECT COUNT(*) FROM users WHERE '火星' NOT IN (SELECT city FROM users)").fetchone()[0]
b = cur.execute(
    "SELECT COUNT(*) FROM users WHERE '火星' NOT IN (SELECT city FROM users WHERE city IS NOT NULL)"
).fetchone()[0]
print(f"   '火星' NOT IN (SELECT city FROM users)                     -> {a} 行")
print(f"   '火星' NOT IN (SELECT city FROM users WHERE city IS NOT NULL) -> {b} 行")
print("   -> 逻辑上「火星」当然不在任何一个城市里，应该返回全部 12 行。")
print("      但第一个查询返回 0 行，而且**不报错**。")
print("      原因：city 列里有 NULL（周杰没填），一遇到 NULL，")
print("            NOT IN 的结果不再是 TRUE/FALSE，而是 NULL（未知），")
print("            于是所有行都被判为「不确定」→ 一行都不返回。")
print()
print("   还有一个反过来的坑：外层那一列自己是 NULL，也会被漏掉：")
c = cur.execute("SELECT user_id, name FROM users WHERE city NOT IN ('北京','上海')").fetchall()
d = cur.execute("SELECT user_id, name FROM users WHERE city IS NULL OR city NOT IN ('北京','上海')").fetchall()
print("      city NOT IN ('北京','上海')                 ->", c)
print("      city IS NULL OR city NOT IN ('北京','上海') ->", d)
print("      -> 第一种漏掉了周杰（他的 city 是 NULL）。")
print("         规律：**NULL 参与任何比较，结果都是 NULL，不是 TRUE 也不是 FALSE。**")
print()

# --- 8. EXISTS：更稳的替代写法 ---
print("=== 8. NOT EXISTS：找没下过单的用户 ===")
e1 = cur.execute(
    "SELECT user_id, name FROM users WHERE user_id NOT IN (SELECT user_id FROM orders)"
).fetchall()
e2 = cur.execute(
    """
    SELECT u.user_id, u.name FROM users u
    WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.user_id)
    """
).fetchall()
print("   NOT IN 版本：   ", e1)
print("   NOT EXISTS 版本：", e2)
print("   -> 这次两者都对，因为 orders.user_id 里没有 NULL。")
print("      怎么确认「有没有 NULL」？用 02 课学的招：")
print("      SELECT COUNT(*), COUNT(user_id) FROM orders —— 两个数相等 = 没有 NULL。")
pin = cur.execute("SELECT COUNT(*), COUNT(user_id) FROM orders").fetchone()
print(f"      实测：COUNT(*) = {pin[0]}，COUNT(user_id) = {pin[1]}  → 安全")
print("   -> 结论：EXISTS 对 NULL 免疫，但别把 NOT IN 一棍子打死 —— 见 8.5。")
print()

# --- 8.5 NOT IN 到底能不能用？先看清风险在哪 ---
print("=== 8.5 NOT IN 的优缺点（别凭听说，看实测）===")
print("   优点：短、可读、字面量列表最自然（NOT IN ('北京','上海') 一眼就懂）")
print("   风险：不来自「写法」，来自 NULL —— 只要集合里或外层列有 NULL，")
print("         判定就变成 UNKNOWN，行被静默丢掉。")
print()
print("   关键：加 IS NOT NULL 只是让「漏掉」变显式，并没有修复语义。实测：")
r1 = cur.execute("SELECT COUNT(*) FROM users WHERE city NOT IN ('北京','上海')").fetchone()[0]
r2 = cur.execute(
    "SELECT COUNT(*) FROM users WHERE city IS NOT NULL AND city NOT IN ('北京','上海')"
).fetchone()[0]
r3 = cur.execute(
    "SELECT COUNT(*) FROM users WHERE city IS NULL OR city NOT IN ('北京','上海')"
).fetchone()[0]
print(f"      city NOT IN ('北京','上海')                      -> {r1} 行（漏掉没填城市的周杰）")
print(f"      city IS NOT NULL AND city NOT IN ('北京','上海')  -> {r2} 行（还是漏，只是漏得「显式」）")
print(f"      city IS NULL OR city NOT IN ('北京','上海')       -> {r3} 行（按业务把空值也算进来）")
print("   -> 所以真正要回答的不是「用哪个函数」，而是：")
print("      **NULL 在业务上算什么？** 「未填写」算不算「非北上用户」？")
print("      定了这个，写法自然就定下来了。")
print()

# --- 8.6 执行计划：性能别靠听说 ---
print("=== 8.6 用 EXPLAIN QUERY PLAN 自己看执行计划 ===")
for label, sql in [
    ("NOT IN 子查询", "SELECT user_id, name FROM users WHERE user_id NOT IN (SELECT user_id FROM orders)"),
    ("NOT EXISTS", "SELECT u.user_id, u.name FROM users u WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.user_id)"),
    ("LEFT JOIN + IS NULL", "SELECT u.user_id, u.name FROM users u LEFT JOIN orders o ON u.user_id = o.user_id WHERE o.order_id IS NULL"),
]:
    print(f"   [{label}]")
    for r in cur.execute("EXPLAIN QUERY PLAN " + sql):
        print("        ", r[-1])
print("   -> 反直觉的地方：SQLite 这里让 NOT IN 走 LIST SUBQUERY（子查询只算一次，")
print("      再做布隆过滤），NOT EXISTS 走 CORRELATED SCALAR SUBQUERY（逐行关联）。")
print("      所以「NOT IN 一定更慢」是错的 —— 快慢取决于优化器、索引和子查询结果集大小。")
print("      想知道你这台数据库怎么选，就 EXPLAIN 一下（MySQL 里用 EXPLAIN，不用 QUERY PLAN）。")
print()

# --- 9. 派生表：把子查询当一张临时表用 ---
print("=== 9. 派生表：子查询放在 FROM 里，必须给别名 ===")
derived = cur.execute(
    """
    SELECT t.status, t.n
    FROM (SELECT status, COUNT(*) AS n FROM orders GROUP BY status) AS t
    WHERE t.n >= 7
    ORDER BY t.n DESC
    """
).fetchall()
print("   ", derived)
print("   -> 括号里的查询先生成一张「临时表」，外层再查它。")
print("      后面那个 AS t 不能省：MySQL 强制要求派生表必须有别名，")
print("      没写会直接报错 Every derived table must have its own alias。")
print()

# --- 10. 子查询 vs JOIN，什么时候用哪个 ---
print("=== 10. 子查询和 JOIN 怎么选 ===")
print("   需要另一张表的【列】放进结果里  -> JOIN")
print("   只需要另一张表的【一个判断结果】-> 子查询 / EXISTS")
print("   要用另一张表的【聚合值】当条件  -> 标量子查询（比 JOIN 后再筛更清楚）")
print()


# ------------------------------------------------------------
# 第二部分：过关任务（在这里作答）
# ------------------------------------------------------------

# TODO 1：用 CASE 把订单分成三档并统计：小额(<200) / 中额(200~1000) / 大额(>=1000)
#         输出三列：档位、订单数、总金额；按金额从低到高排列
#         结果存给 rows_case
#CASE 是一个被选择的目标，返回THEN 后面的值
rows_case = cur.execute(
    """SELECT
        CASE WHEN amount < 200 THEN '小额'
             WHEN amount < 1000 THEN '中额'
             ELSE '大额'
             END AS 挡位,
        COUNT(*), SUM(amount)
    FROM orders
    GROUP BY 挡位
    ORDER BY MIN(amount)
    """).fetchall()

# TODO 2：金额高于「全表平均金额」的订单有多少笔？存给 n_above（数字，不是列表）
#         要求：平均金额必须用子查询拿到，不许自己先算好写死
n_above = cur.execute("""
    SELECT COUNT(*)
    FROM orders
    WHERE amount > (SELECT AVG(amount) FROM orders)""").fetchone()[0]

# TODO 3：用 NOT IN + 子查询找出「从没下过订单的用户」（user_id, name）
#         结果存给 via_not_in
#         然后写注释回答：这次的 NOT IN 为什么是安全的？
via_not_in = cur.execute("SELECT user_id, name FROM users WHERE user_id NOT IN (SELECT user_id FROM orders)").fetchall()
# 你的解释：因为子查询 SELECT user_id FROM orders 里没有 NULL，NOT IN 不会因 NULL 变成 UNKNOWN

# TODO 4：各状态的订单占比。输出三列：状态、订单数、占比（保留 1 位小数）
#         按占比从大到小排。分母用子查询拿全表总数
#         结果存给 rows_pct
rows_pct = cur.execute("""
    SELECT status, COUNT(*), ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM orders), 1)
    FROM orders
    GROUP BY status
    ORDER BY COUNT(*) DESC""").fetchall()

# TODO 5（不写代码，写在注释里）：
#         ① CASE 忘了写 ELSE，没被任何 WHEN 命中的行会得到什么值？
#         ② 用 city NOT IN ('北京','上海') 找「非北上用户」时，谁会被漏掉？怎么修？
# 你的答案：None,city是空值的用户会被漏掉，前面加个或条件IS NULL


# ------------------------------------------------------------
# 第三部分：自检区（不要改）
# ------------------------------------------------------------
print("===== 自检 =====")
print("TODO1 rows_case ->", rows_case)
print("      | 期望 [('小额', 11, 1578.0), ('中额', 25, 11755.0), ('大额', 4, 6291.0)]")
print()
print("TODO2 n_above ->", n_above, "| 期望 13")
print()
print("TODO3 via_not_in ->", via_not_in, "| 期望 [(12, '马丽')]")
print()
print("TODO4 rows_pct ->", rows_pct)
print("      | 期望 [('paid', 18, 45.0), ('pending', 9, 22.5), ('cancelled', 7, 17.5), ('refunded', 6, 15.0)]")
print()
print("全对的话，你已经能把「条件」和「嵌套查询」写进 SQL 里了。")
print("下一课 05：窗口函数（面试最爱考的那一类）。")
