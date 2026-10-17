# ============================================================
# SQL 07：面试真题综合 —— 6 道业务题，不给 SQL 提示
# 用法：右键 -> Run '07_interview'
# 数据库：practice.db（同目录）
#
# 【本课没有新语法】
#   全部是 01–06 的组合：聚合、分组、JOIN、子查询、CASE、窗口、NULL。
#   这课练的是另一件事：**从「业务描述」翻译成 SQL 的能力**。
#
# 【面试真实场景】
#   面试官不会给你 SQL 骨架，只会说：
#     「运营想看每个月的 GMV 环比，还要能看出有没有下滑」
#   你要做的第一件事不是写 SQL，是**复述需求 + 确认口径**。
#
# 【解题五问：以后每道题都先过一遍】
#   ① 这一行代表谁？            -> 决定要不要 GROUP BY、按什么分组
#   ② 谁必须出现？              -> 决定主表是谁、INNER 还是 LEFT JOIN
#   ③ 要不要在每个组里算一个数？ -> 决定用不用聚合（COUNT/SUM/AVG）
#   ④ 要不要「明细里带统计」或「排名/环比」？ -> 只有窗口函数能干
#   ⑤ 有没有 NULL 风险？        -> != / NOT IN / SUM / 拼接，四个地方都要想一下
# ============================================================

import sqlite3
from pathlib import Path

DB = Path(__file__).with_name("practice.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()


# ------------------------------------------------------------
# 第一部分：示范 —— 从业务描述到 SQL 的完整过程
# ------------------------------------------------------------
print("=== 示范题：卖得最好的商品是哪个？它占全站销售额多少？ ===")
print()

print("第 1 步 复述需求：找出「按商品汇总的销售额」里最大的那个，并算它占全店的比例。")
print()
print("第 2 步 过一遍五问：")
print("   ① 一行代表谁？        一个商品 -> 按商品分组")
print("   ② 谁必须出现？        只要「卖出去过」的商品 -> 主表 orders，INNER JOIN products")
print("   ③ 算一个数？          每个商品的 SUM(amount)")
print("   ④ 要窗口吗？          占比的分母是「全站总额」-> 标量子查询更简单，不用窗口")
print("   ⑤ NULL 风险？         商品名/金额都非空；但比例要做除法，注意别用整数除法")
print()

print("第 3 步 先写「主体」，再补「占比」：")
demo = cur.execute(
    """
    SELECT p.product_name,
           SUM(o.amount) AS gmv,
           ROUND(SUM(o.amount) * 100.0 / (SELECT SUM(amount) FROM orders), 1) AS share
    FROM orders o
    JOIN products p ON o.product_id = p.product_id
    GROUP BY p.product_id, p.product_name
    ORDER BY gmv DESC
    LIMIT 1
    """
).fetchall()
for name, gmv, share in demo:
    print(f"   {name}  销售额 {gmv}  占全站 {share}%")
print()

print("第 4 步 用手算校验（这一步别省，它救过很多人）：")
total = cur.execute("SELECT SUM(amount) FROM orders").fetchone()[0]
print(f"   6487 / {total} = {6487 / total:.4f} -> {6487 / total * 100:.1f}%  与上面的 share 一致 ✅")
print("   -> 面试时如果你能主动说「我用手算核对了一下比例」，这就是差异点。")
print()


# ------------------------------------------------------------
# 第二部分：六道真题（自己写，不给 SQL）
# ------------------------------------------------------------
# 建议分两次做，每题写完先跑一次看自检区，再往下。

# TODO 1【GMV 口径】
#   运营只看「有效订单」：状态为 paid 或 pending 的算有效，cancelled / refunded 不算。
#   请给出三个数：有效订单数、有效 GMV、客单价（GMV ÷ 订单数，保留 2 位小数）。
#   变量名：n_valid / gmv_valid / aov_valid
n_valid = cur.execute("SELECT COUNT(*) FROM orders WHERE status = 'paid' OR status = 'pending' ").fetchone()[0]
gmv_valid = cur.execute("SELECT SUM(amount) FROM orders WHERE status = 'paid' OR status = 'pending'").fetchone()[0]
aov_valid = cur.execute("SELECT ROUND(AVG(amount), 2) FROM orders WHERE status = 'paid' OR status = 'pending'").fetchone()[0]

# TODO 2【月度 GMV 与环比】
#   按自然月统计有效 GMV，并算出与上个月的环比增长率（百分比，保留 1 位小数）。
#   第一个月没有上个月，环比留空（NULL）。
#   变量名：rows_mom（共 6 行，按月份升序）
#   提示：环比必须用窗口函数 LAG；公式是 (本月 - 上月) / 上月 * 100
rows_mom = cur.execute(
    """WITH t AS (SELECT strftime('%Y-%m', order_date) AS time, SUM(amount) AS gmv
                FROM orders
                WHERE status = 'paid' OR status = 'pending'
                GROUP BY time)
    SELECT time, gmv, 
        ROUND (gmv * 100 / LAG(gmv) OVER(ORDER BY time) - 100 , 1)
    FROM t
    ORDER BY time""").fetchall()

# TODO 3【用户分层】
#   按每个用户的「已支付总额（paid）」分三档：
#     >= 2000 高价值 / >= 800 中价值 / 其余低价值
#   没下过单、或没有 paid 订单的用户，总额算 0，也要落进低价值。
#   统计各档人数，按人数从多到少排。
#   变量名：rows_tier
rows_tier = cur.execute(
    """WITH t AS (SELECT u.user_id, 
            SUM(CASE WHEN o.status = 'paid' THEN o.amount ELSE 0 END) AS total
            FROM users u
            LEFT JOIN orders o ON o.user_id = u.user_id
            GROUP BY u.user_id)
    SELECT CASE WHEN total >= 2000 THEN '高价值'
         WHEN total >= 800 THEN '中价值'
         ELSE '低价值'
        END AS 挡位, COUNT(*)
    FROM t
    GROUP BY 挡位
    ORDER BY COUNT(*) DESC """).fetchall()

# TODO 4【复购率】
#   在 paid 订单里，下过 2 笔及以上的用户算「复购用户」。
#   请给出：有 paid 订单的用户数、复购用户数、复购率（百分比，保留 1 位小数）。
#   变量名：paid_users / repeat_users / repeat_rate
paid_users = cur.execute("SELECT COUNT(DISTINCT user_id) FROM orders WHERE status = 'paid'").fetchone()[0]
repeat_users = cur.execute(
    """WITH a AS (SELECT COUNT(*) AS times, user_id
                  FROM orders 
                  WHERE status = 'paid' 
                  GROUP BY user_id 
                  HAVING COUNT(*) >= 2)
    SELECT COUNT(user_id)
    FROM a"""
).fetchone()[0]
repeat_rate = repeat_users *100.0 / paid_users

# TODO 5【每城市 Top1】
#   每个城市里订单数最多的那个用户是谁？给出：城市、user_id、姓名、订单数。
#   城市为空的用户单独成一组，也要保留。每个城市只留 1 个；
#   订单数并列时，按 user_id 小的优先（保证结果可复现）。
#   变量名：rows_city_top（共 6 行，按城市升序；注意 NULL 城市会排最前）
rows_city_top = cur.execute(
    """WITH a AS (SELECT COALESCE(u.city, 'None') AS City, u.user_id, u.name, COUNT(order_id) AS n, 
                         ROW_NUMBER() OVER (PARTITION BY u.city ORDER BY COUNT(o.order_id) DESC, u.user_id) AS rn
                  FROM users u
                  LEFT JOIN orders o ON o.user_id = u.user_id
                  GROUP BY u.user_id)
    SELECT City, user_id, name, n
    FROM a
    WHERE rn = 1
    ORDER BY City """).fetchall()



# TODO 6【类目占比】
#   每个商品类目的销售额、以及它占全站销售额的比例（百分比，保留 1 位小数），
#   按销售额从高到低排。
#   变量名：rows_cat_share
rows_cat_share = cur.execute(
    """SELECT p.category, SUM(o.amount),ROUND(SUM(amount) *100.0 / SUM(SUM(o.amount)) OVER() , 1)
    FROM orders o
    LEFT JOIN products p ON o.product_id = p.product_id
    GROUP BY category
    ORDER BY SUM(o.amount) DESC 
    """).fetchall()

# TODO 7（不写代码，写在注释里）
#   面试官问：「cancelled 和 refunded 的订单，要不要计入 GMV？」
#   你会怎么回答？（提示：这题没有标准答案，考的是你会不会先确认口径）
# 你的答案：不计入，cancelled和refunded实际上没有完成交易，记录在订单中多数是为了确认货品的走向，订单取消后也不应删除，所以留在数据库中


# ------------------------------------------------------------
# 第三部分：自检区（不要改）
# ------------------------------------------------------------
print("===== 自检 =====")
print("TODO1 n_valid   ->", n_valid, "| 期望 27")
print("TODO1 gmv_valid ->", gmv_valid, "| 期望 13922.0")
print("TODO1 aov_valid ->", aov_valid, "| 期望 515.63")
print()
print("TODO2 rows_mom ->", rows_mom)
print("      | 期望 [('2024-07',1681.0,None), ('2024-08',3182.0,89.3), ('2024-09',5174.0,62.6), ('2024-10',1497.0,-71.1), ('2024-11',1256.0,-16.1), ('2024-12',1132.0,-9.9)]")
print()
print("TODO3 rows_tier ->", rows_tier)
print("      | 期望 [('低价值',9), ('高价值',2), ('中价值',1)]")
print()
print("TODO4 paid_users   ->", paid_users, "| 期望 10")
print("TODO4 repeat_users ->", repeat_users, "| 期望 5")
print("TODO4 repeat_rate  ->", repeat_rate, "| 期望 50.0")
print()
print("TODO5 rows_city_top ->", rows_city_top)
print("      | 期望 [(None,8,'周杰',2), ('上海',2,'王芳',5), ('北京',1,'张伟',4), ('广州',4,'刘强',7), ('成都',9,'吴磊',3), ('深圳',11,'孙悦',6)]")
print()
print("TODO6 rows_cat_share ->", rows_cat_share)
print("      | 期望 [('运动',9595.0,48.9), ('数码',7110.0,36.2), ('家居',2385.0,12.2), ('生活',534.0,2.7)]")
print()
print("六道全对，你的 SQL 已经能应付数据岗笔试的大部分题了。")
print("下一课 08：MySQL 实操（建库建表、把练习迁过去、记下和 SQLite 的差异）。")
