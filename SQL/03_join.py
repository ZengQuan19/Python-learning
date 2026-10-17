# ============================================================
# SQL 03：多表 JOIN —— 把两张表拼起来
# 用法：右键 -> Run '03_join'
# 数据库：practice.db（同目录）
#
# 【本课要学什么】
#   orders 表里只有 user_id（编号），你根本看不出是谁下的单；
#   users 表里才有姓名。想把「谁 + 买了什么」放在一起看，就得 JOIN。
#
#   INNER JOIN  只保留两边都匹配上的行
#   LEFT  JOIN  保留左表全部，右表没匹配上的地方填 NULL
#   ON          写「两边的编号怎么对上」
#
# 【面试频率 ★★★★★】
#   数据岗面试只要涉及多张表，第一句就是「这两张表怎么关联」。
#
# 【本课新词】
#   主键 / 外键 / 连接列 / 表别名 / 1:N 放大 / LEFT JOIN 之后的 NULL
# ============================================================

import sqlite3
from pathlib import Path

from narwhals import coalesce

DB = Path(__file__).with_name("practice.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()


# ------------------------------------------------------------
# 第一部分：热身（不用改，直接运行）
# ------------------------------------------------------------

# --- 1. 为什么非要 JOIN ---
print("=== 1. 光看 orders，你不知道这些单子是谁下的 ===")
print("   ", cur.execute("SELECT order_id, user_id, amount FROM orders LIMIT 3").fetchall())
print("   -> user_id 只是 1、2、3 这种编号，人名在 users 表里。")
print("      这就是关系型数据库的做法：数据分表存，用编号互相指。")
print("      users.user_id 是主键（唯一标识一个用户），")
print("      orders.user_id 是指向它的外键（说这笔单属于哪个用户）。")
print()

# --- 2. JOIN 基本写法 ---
print("=== 2. 第一次 JOIN ===")
rows = cur.execute(
    """
    SELECT o.order_id, u.name, o.amount
    FROM orders o
    JOIN users  u ON o.user_id = u.user_id
    ORDER BY o.order_id
    LIMIT 3
    """
).fetchall()
print("   ", rows)
print("   语法拆开看：")
print("     FROM orders o         <- 主表，o 是它的别名")
print("     JOIN users  u         <- 要拼进来的表，u 是别名")
print("     ON o.user_id = u.user_id  <- 连接条件：两边的编号怎么对上")
print("   -> ON 就是「这两张表的哪两列说的是同一件事」。")
print()

# --- 3. 为什么必须有表别名 ---
print("=== 3. 两张表都有 user_id，不写前缀就会歧义 ===")
try:
    cur.execute("SELECT user_id FROM orders o JOIN users u ON o.user_id = u.user_id")
except sqlite3.OperationalError as e:
    print("   报错原文：", e)
    print("   -> 数据库不知道你要哪张表的 user_id。解决办法：写 o.user_id 或 u.user_id。")
    print("      别名（o / u）就是为了这个：让每一列都能说清自己来自哪张表。")
print()

# --- 4. INNER JOIN 会丢掉「没匹配上」的人 ---
print("=== 4. 马丽去哪了：INNER JOIN 只留匹配上的 ===")
print("   全部用户数：", cur.execute("SELECT COUNT(*) FROM users").fetchone()[0])
inner = cur.execute(
    "SELECT COUNT(DISTINCT u.user_id) FROM users u JOIN orders o ON u.user_id = o.user_id"
).fetchone()[0]
print("   JOIN 之后出现过的用户数：", inner)
print("   -> 少了 1 个：马丽（12 号）一笔订单都没有，INNER JOIN 直接把她扔掉了。")
print("      想让她留下来，用 LEFT JOIN。")
print()

# --- 5. LEFT JOIN：保留左表全部 ---
print("=== 5. LEFT JOIN：左表的每一行都留下 ===")
print("   马丽那一行长这样（右边全是 NULL）：")
for r in cur.execute(
    """
    SELECT u.user_id, u.name, o.order_id, o.amount
    FROM users u
    LEFT JOIN orders o ON u.user_id = o.user_id
    WHERE u.user_id = 12
    """
).fetchall():
    print("     ", r)
print("   -> 「右边全是 NULL」就是 LEFT JOIN 留下的痕迹。")
print("      所以「找出没有下过单的人」有固定套路：")
print("      LEFT JOIN 之后加 WHERE 右表的连接列 IS NULL。")
print("      （用 IS NULL，不要用 = NULL —— 后者永远不成立，还不报错）")
print()

# --- 6. 陷阱①：JOIN 之后行数会被放大 ---
print("=== 6. 陷阱①：JOIN 之后 COUNT(*) 会骗你 ===")
n_users = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
n_orders = cur.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
all_cnt = cur.execute(
    "SELECT COUNT(*) FROM users u LEFT JOIN orders o ON u.user_id = o.user_id"
).fetchone()[0]
ord_cnt = cur.execute(
    "SELECT COUNT(o.order_id) FROM users u LEFT JOIN orders o ON u.user_id = o.user_id"
).fetchone()[0]
dis_cnt = cur.execute(
    "SELECT COUNT(DISTINCT u.user_id) FROM users u LEFT JOIN orders o ON u.user_id = o.user_id"
).fetchone()[0]
print(f"   users 表本身       有 {n_users} 行")
print(f"   orders 表本身      有 {n_orders} 行")
print(f"   LEFT JOIN 之后     有 {all_cnt} 行  <- 12 个人被 40 笔订单撑开了")
print(f"   COUNT(*)           = {all_cnt}   （数的是「拼完的行」，不是人）")
print(f"   COUNT(o.order_id)  = {ord_cnt}   （NULL 被跳过，正好是订单数）")
print(f"   COUNT(DISTINCT u.user_id) = {dis_cnt}   （去重后才是真正的人数）")
print("   -> 教训：JOIN 之后想数『人』，别用 COUNT(*)。")
print("      要么 COUNT(DISTINCT 用户id)，要么回原表数。")
print("      这正是 02 课「COUNT(*) 和 COUNT(列) 不是一回事」在 JOIN 场景下的续集。")
print()

# --- 7. 陷阱②：连接列写错，不报错，结果荒谬 ---
print("=== 7. 陷阱②：ON 写错列，SQL 不会报错 ===")
wrong = cur.execute("SELECT * FROM orders o JOIN users u ON o.order_id = u.user_id").fetchall()
right = cur.execute("SELECT * FROM orders o JOIN users u ON o.user_id = u.user_id").fetchall()
print(f"   正确连接（o.user_id = u.user_id）：{len(right)} 行")
print(f"   错误连接（o.order_id = u.user_id）：{len(wrong)} 行  <- 居然也跑出来了")
print("   -> 订单号跟用户号当然对不上，只是巧合match上了 12 行。")
print("      没有任何报错，结果完全是垃圾 —— 这就是静默失败。")
print("      防线：JOIN 前后各数一次行数，心里先有预期。")
print()

# --- 8. 陷阱③：LEFT JOIN 之后聚合函数遇到 NULL ---
print("=== 8. 陷阱③：LEFT JOIN 之后 SUM 会给你 NULL ===")
a = cur.execute(
    """
    SELECT u.name, SUM(o.amount)
    FROM users u LEFT JOIN orders o ON u.user_id = o.user_id
    GROUP BY u.user_id HAVING u.user_id = 12
    """
).fetchone()
b = cur.execute(
    """
    SELECT u.name, COALESCE(SUM(o.amount), 0)
    FROM users u LEFT JOIN orders o ON u.user_id = o.user_id
    GROUP BY u.user_id HAVING u.user_id = 12
    """
).fetchone()
print("   直接 SUM(o.amount)：", a, "  <- NULL，不是 0")
print("   套上 COALESCE(...,0)：", b)
print("   -> 没订单的人，他的金额和是「不知道」还是「0」？业务上通常是 0。")
print("      COALESCE 的作用：遇到 NULL 就换成你给的替身值。")
print()

# --- 9. 完整例子：每个用户的订单数、总金额 ---
print("=== 9. JOIN + GROUP BY：每个用户的订单数和总金额 ===")
final = cur.execute(
    """
    SELECT u.name, COUNT(o.order_id) AS n, COALESCE(SUM(o.amount), 0) AS total
    FROM users u
    LEFT JOIN orders o ON u.user_id = o.user_id
    GROUP BY u.user_id, u.name
    ORDER BY total DESC
    """
).fetchall()
print(f"{'姓名':<8}{'单数':>6}{'总额':>10}")
for name, n, total in final:
    print(f"{name:<8}{n:>6}{total:>10.1f}")
print("   -> 注意 GROUP BY 里写了 u.user_id, u.name 两个：")
print("      SELECT 里出现的非聚合列，都要放进 GROUP BY（粒度那一课讲过）。")
print()

# ⚠️【本节最容易卡住的一处理解】为什么「统计订单」却按 users 的列分组？
#
#   GROUP BY 决定的是「一行代表谁」，不是「数据来自哪张表」。
#   这次的需求是「每个用户一行」，所以分组列必须是【用户的标识】—— u.user_id。
#
#   JOIN + GROUP BY 的查询里，三个位置各有分工，别混：
#     FROM 后面的主表    -> 决定「谁必须出现」    这里是 users（12 个人一个都不能少）
#     GROUP BY 后面的列  -> 决定「一行代表谁」    这里是 u.user_id（一个用户一行）
#     SELECT 里的聚合列  -> 决定「统计什么」      这里是 o.order_id / o.amount（统计订单）
#
#   一句话：被【描述】的是「用户」，被【统计】的是「订单」，由不同位置分别承担。
#
#   为什么主表必须是 users 而不是 orders？看下面这组对照（真实数据）：
#     FROM orders GROUP BY o.user_id                   -> 11 行，马丽消失
#     FROM users u LEFT JOIN orders o
#          GROUP BY u.user_id, u.name                  -> 12 行，马丽 (12, '马丽', 0, 0)
#   因为 orders 里根本没有马丽的任何一行 —— join 之前她就不存在，
#   而需求说的是「每个用户」，那"用户的名单"只能来自 users 表。
#
#   还有一个更隐蔽的错法（行数看着对，内容错）：
#     FROM users u LEFT JOIN orders o GROUP BY o.user_id
#       -> 也是 12 行，但马丽会变成一个 (None, 1) 的组：身份变成了 NULL，
#          而且计数是 1 不是 0 —— 因为 LEFT JOIN 也给她留了一行（右边全是 NULL）。
#          所以 LEFT JOIN 之后统计必须写 COUNT(o.order_id)（= 0），
#          不能写 COUNT(*)（= 1）。这是 COUNT(*) 与 COUNT(列) 的第三次交手了。
print()


# ------------------------------------------------------------
# 第二部分：过关任务（在这里作答）
# ------------------------------------------------------------

# TODO 1：INNER JOIN 出「订单 + 下单人姓名」：
#         order_id、name、amount 三列，按 order_id 升序，只要前 5 条
#         结果存给 rows1
rows1 = cur.execute(
    """SELECT o.order_id, u.name, o.amount
    FROM users u
    JOIN orders o ON u.user_id = o.user_id
    ORDER BY o.order_id
    LIMIT 5""").fetchall()

# TODO 2：用 LEFT JOIN 找出「从没下过订单的用户」，
#         要 user_id 和 name 两列。结果存给 no_order_users
#         提示：LEFT JOIN 之后，右表连接列为 NULL 的那些就是。
cur.execute(
    """SELECT u.user_id, u.name
    FROM users u
    LEFT JOIN orders o ON u.user_id = o.user_id
    WHERE o.order_id IS NULL
    GROUP BY u.user_id, u.name""")
no_order_users = cur.fetchall()

# TODO 3：每个用户的「姓名 + 订单数 + 总金额」，
#         按总金额从大到小排（没订单的人也要在，总额算 0）
#         结果存给 user_totals
#         提示：LEFT JOIN + GROUP BY + COALESCE；想清楚 GROUP BY 后面写什么。
cur.execute(
    """SELECT u.name, COUNT(o.order_id), COALESCE(SUM(o.amount), 0)
    FROM users u
    LEFT JOIN orders o ON u.user_id = o.user_id
    GROUP BY u.user_id, u.name
    """)
user_totals = cur.fetchall()

# TODO 4：找出「从来没被卖出过的商品」，要 product_id 和 product_name
#         结果存给 never_sold
#         提示：products 和 orders 之间用哪个列连接？谁是左表？
cur.execute(
    """SELECT p.product_id, p.product_name
    FROM products p
    LEFT JOIN orders o ON p.product_id = o.product_id
    WHERE o.product_id IS NULL
    """)
never_sold = cur.fetchall()

# TODO 5：数行数，三个变量都要是数字（不是列表）
#         - cnt_all   ：users LEFT JOIN orders 之后的 COUNT(*)
#         - cnt_order ：同一个 JOIN 下的 COUNT(o.order_id)
#         - cnt_user  ：同一个 JOIN 下 COUNT(DISTINCT u.user_id)
#         然后在下面写注释回答：为什么这三个数各不相同？
cnt_all = cur.execute("SELECT COUNT(*) FROM users u LEFT JOIN orders o ON o.user_id = u.user_id").fetchone()[0]
cnt_order = cur.execute("SELECT COUNT(o.order_id) FROM users u LEFT JOIN orders o ON o.user_id = u.user_id").fetchone()[0]
cnt_user = cur.execute("SELECT COUNT(DISTINCT u.user_id) FROM users u LEFT JOIN orders o ON o.user_id = u.user_id").fetchone()[0]
# 你的解释：COUNT(*)计算的是行数，而指定具体的列则计算时NULL不会做任何处理，行数从1->0，而DISTINCT会消除所有重复的指定内容只保留一个


# ------------------------------------------------------------
# 第三部分：自检区（不要改）
# ------------------------------------------------------------
print("===== 自检 =====")
print("TODO1 rows1 ->", rows1)
print("      | 期望 [(1,'孙悦',399.0), (2,'刘强',129.0), (3,'王芳',477.0), (4,'刘强',129.0), (5,'孙悦',1497.0)]")
print()
print("TODO2 no_order_users ->", no_order_users, "| 期望 [(12, '马丽')]")
print()
print("TODO3 user_totals 行数 ->", len(user_totals) if user_totals is not None else None, "| 期望 12")
print("      第一行 ->", user_totals[0] if user_totals else None, "| 期望 ('孙悦', 6, 4898.0)")
print("      最后一行 ->", user_totals[-1] if user_totals else None, "| 期望 ('马丽', 0, 0)")
print()
print("TODO4 never_sold ->", never_sold, "| 期望 [(108, '笔记本')]")
print()
print("TODO5 cnt_all   ->", cnt_all, "| 期望 41（拼完的行数）")
print("TODO5 cnt_order ->", cnt_order, "| 期望 40（NULL 被跳过）")
print("TODO5 cnt_user  ->", cnt_user, "| 期望 12（去重后的真人数）")
print()
print("全对的话，多表查询你就入门了 —— 面试里「这两张表怎么关联」你能答上来。")
print("下一课 04：子查询 + CASE WHEN，把条件写进查询里面。")
