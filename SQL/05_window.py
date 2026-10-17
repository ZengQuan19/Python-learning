# ============================================================
# SQL 05：窗口函数 —— 既保留明细，又附上统计
# 用法：右键 -> Run '05_window'
# 数据库：practice.db（同目录）
#
# 【本课解决的核心矛盾】
#   GROUP BY 会把明细行「压掉」：40 笔订单 → 11 行（一个人一行）。
#   但真实需求经常是「既要明细，又要统计」：
#     每一笔订单 + 这个用户的总金额 + 这笔在他所有订单里排第几 + 比上一笔多多少
#   窗口函数就是干这个的：**不减少行数**，在旁边多挂几列统计值。
#
# 【面试频率 ★★★★★】
#   「每个用户金额最高的一单」「组内排名」「环比」「累计」—— 全是窗口函数。
#   而且面试官特别爱问 ROW_NUMBER / RANK / DENSE_RANK 的区别。
#
# 【本课新词】
#   OVER / PARTITION BY / ROW_NUMBER / RANK / DENSE_RANK / LAG
#   累计求和 / CTE（WITH ... AS）
# ============================================================

import sqlite3
from pathlib import Path

DB = Path(__file__).with_name("practice.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()


# ------------------------------------------------------------
# 第一部分：热身（不用改，直接运行）
# ------------------------------------------------------------

# --- 1. 先看清 GROUP BY 的「副作用」---
print("=== 1. GROUP BY 会把明细丢掉 ===")
n_group = len(cur.execute("SELECT user_id, SUM(amount) FROM orders GROUP BY user_id").fetchall())
print(f"   GROUP BY 之后：{n_group} 行（一个人一行，40 笔明细没了）")
print("   -> 可我想要的是：每一笔订单后面，跟着它所属用户的总金额。")
print("      明细要留，统计也要有 —— GROUP BY 做不到，窗口函数可以。")
print()

# --- 2. 第一个窗口函数 ---
print("=== 2. 第一个窗口函数：把「每人总额」贴回每一笔订单 ===")
rows = cur.execute(
    """
    SELECT order_id, user_id, amount,
           SUM(amount) OVER (PARTITION BY user_id) AS user_total,
           COUNT(*)    OVER (PARTITION BY user_id) AS user_cnt
    FROM orders
    ORDER BY order_id
    LIMIT 5
    """
).fetchall()
for r in rows:
    print("   ", r)
print("   -> 行数还是 40（明细一行不少），只是在旁边多了两列统计值。")
print("      语法拆开：")
print("         SUM(amount)  <- 用哪个聚合函数（跟 GROUP BY 一样的那几个）")
print("         OVER (...)   <- 关键！告诉 SQL「这是一个窗口函数」")
print("         PARTITION BY user_id  <- 在什么范围内分组（像 GROUP BY，但不合并行）")
print("      读作：算金额总和，但按 user_id 分成几个窗口，每个窗口各算一次。")
print()

# --- 3. 三种排名函数（面试必考）---
print("=== 3. ROW_NUMBER / RANK / DENSE_RANK 的区别 ===")
rank_demo = cur.execute(
    """
    SELECT order_id, amount,
           ROW_NUMBER() OVER (ORDER BY amount DESC) AS rn,
           RANK()       OVER (ORDER BY amount DESC) AS rk,
           DENSE_RANK() OVER (ORDER BY amount DESC) AS dr
    FROM orders WHERE user_id = 4
    ORDER BY amount DESC
    """
).fetchall()
print(f"   {'订单':<6}{'金额':>8}{'ROW_NUMBER':>12}{'RANK':>6}{'DENSE_RANK':>12}")
for oid, amt, rn, rk, dr in rank_demo:
    print(f"   {oid:<6}{amt:>8}{rn:>12}{rk:>6}{dr:>12}")
print("   -> 这个用户有两笔 998（并列第 1）、两笔 129（并列最后），正好看差异：")
print("      ROW_NUMBER：永远不重复，1 2 3 4 5 6 7 —— 并列也硬排先后")
print("      RANK：并列同名次，但会「跳号」—— 1 1 3（第 2 名被占了）")
print("      DENSE_RANK：并列同名次，不跳号 —— 1 1 2")
print("      业务含义：要「必须挑出一个」用 ROW_NUMBER；")
print("                要「并列的都算第一」用 RANK / DENSE_RANK。")
print()
# ⚠️ 别把这三个名字当成「数据」——它们是【函数】，概念分三层：
#     函数名（动作）  ROW_NUMBER() / RANK() / SUM() / LAG()   <- 你调用它，它算出数字
#     关键字（零件）  OVER / PARTITION BY / ORDER BY          <- 告诉 SQL 这个函数怎么算
#     列名（别名）    AS 名次                                 <- 【你】给结果列起的名字
#   函数算出来的那些数字，最后表现为结果里的一列数据 —— 那一列的名字由 AS 决定：
#     不起别名时，列名会是整串表达式：'ROW_NUMBER() OVER (ORDER BY order_id)'（很难看）
#   两个实测结论：
#     ① 排名函数【必须】配 OVER 才能用：SELECT ROW_NUMBER() FROM orders
#        -> 报错 misuse of window function ROW_NUMBER()
#     ② SUM 是「两栖」的：不带 OVER（配 GROUP BY）= 聚合，吃掉行；
#        带 OVER = 窗口，保留行。
#        SELECT order_id, amount, SUM(amount) OVER () AS total FROM orders  -> 3 行
#        SELECT SUM(amount) FROM orders                                     -> 1 行
print()

# --- 4. 累计陷阱：带上 ORDER BY 的聚合窗口会变成「累计」---
print("=== 4. 坑①：SUM() OVER (ORDER BY ...) 是累计，不是总计 ===")
cum_demo = cur.execute(
    """
    SELECT order_id, amount,
           SUM(amount) OVER (ORDER BY order_id) AS 累计,
           SUM(amount) OVER ()                  AS 总计
    FROM orders ORDER BY order_id LIMIT 3
    """
).fetchall()
for oid, amt, cum, tot in cum_demo:
    print(f"   订单{oid}  金额{amt:>8}  累计{cum:>10}  总计{tot:>10}")
print("   -> 同一个 SUM，只因为里面多了一句 ORDER BY，含义就变了：")
print("      带 ORDER BY  -> 从第一行累加到当前行（累计/滚动）")
print("      不带 ORDER BY -> 整个窗口的总和（总计）")
print("      ⚠️ 很多人想要「总计」，却顺手写了 ORDER BY，拿到一串累计值，还不报错。")
print()
# --- 5. 坑②：窗口函数不能写在 WHERE 里 ---
print("=== 5. 坑②：窗口函数不能放进 WHERE ===")
try:
    cur.execute("SELECT order_id FROM orders WHERE ROW_NUMBER() OVER (ORDER BY order_id) = 1")
except sqlite3.OperationalError as e:
    print("   报错原文：", e)
print("   -> 为什么？执行顺序决定的：")
print("      FROM -> WHERE -> GROUP BY -> HAVING -> SELECT -> ORDER BY -> LIMIT")
print("      窗口函数是在 SELECT 阶段才算的，而 WHERE 比它早 —— 那时它还不存在。")
print("      解法：用 CTE（WITH ... AS）把查询包一层，先算出名次，外层再筛。")
print()

# --- 6. 经典套路：每个用户金额最高的一单 ---
print("=== 6. 经典题：每个用户金额最高的一单（用 CTE 包一层）===")
top = cur.execute(
    """
    WITH t AS (
        SELECT user_id, order_id, amount,
               RANK() OVER (PARTITION BY user_id ORDER BY amount DESC) AS rk
        FROM orders
    )
    SELECT user_id, order_id, amount FROM t WHERE rk = 1 ORDER BY user_id
    """
).fetchall()
print(f"   用 RANK：{len(top)} 行（有人并列第一，都留下了）")
print("   ", top[:4], "...")
top_rn = cur.execute(
    """
    WITH t AS (
        SELECT user_id, order_id,
               ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY amount DESC) AS rn
        FROM orders
    )
    SELECT user_id, order_id FROM t WHERE rn = 1 ORDER BY user_id
    """
).fetchall()
print(f"   用 ROW_NUMBER：{len(top_rn)} 行（每人只留一条）")
print("   -> 同一道题，两个函数差 2 行。**这不是对错问题，是业务问题**：")
print("      并列第一要不要都留？面试答出这一句，比背语法值钱。")
print()

# --- 7. LAG：和「上一行」比较（环比/间隔）---
print("=== 7. LAG：看同一用户相邻两单的金额 ===")
lag_rows = cur.execute(
    """
    SELECT order_id, order_date, amount,
           LAG(amount) OVER (ORDER BY order_date) AS prev_amount
    FROM orders WHERE user_id = 4
    ORDER BY order_date
    """
).fetchall()
print(f"   {'订单':<6}{'日期':<14}{'金额':>8}{'上一单':>10}")
for oid, d, amt, prev in lag_rows:
    print(f"   {oid:<6}{d:<14}{amt:>8}{str(prev):>10}")
print("   -> LAG = 取「上一行」的值；LEAD = 取下一行。算术在这里就活了：")
print("      amount - LAG(amount) 就是环比；order_date 相减就是间隔天数。")
print("      注意：每个用户的第一行没有「上一单」，所以是 None。")
print()

# --- 8. 什么时候用窗口函数、什么时候用 GROUP BY ---
print("=== 8. 怎么选 ===")
print("   结果是「一个组一行」          -> GROUP BY")
print("   结果是「明细一行都不少 + 统计」-> 窗口函数")
print("   要排名 / 累计 / 和上一行比     -> 只能窗口函数")
print()


# ------------------------------------------------------------
# 第二部分：过关任务（在这里作答）
# ------------------------------------------------------------

# TODO 1：给每笔订单加上两列统计：该用户的总金额、该用户的订单数
#         输出 order_id, user_id, amount, 该用户总额, 该用户订单数
#         按 order_id 排，只取前 5 条。结果存给 rows_win
#         要求：行数必须还是 40（窗口函数不会压行）
rows_win = cur.execute(
    """SELECT order_id, user_id, amount,
            SUM(amount) OVER(PARTITION BY user_id), 
            COUNT(*) OVER(PARTITION BY user_id)
        FROM orders
        ORDER BY order_id""").fetchall()

# TODO 2：找出每个用户金额最高的那一笔订单，并列第一的都要保留
#         输出 user_id, order_id, amount，按 user_id 排序。结果存给 rows_top
#         提示：窗口函数不能写在 WHERE 里，先想想怎么包一层。
rows_top = cur.execute(
    """WITH t AS (SELECT user_id, order_id, amount,
                RANK() OVER (PARTITION BY user_id ORDER BY amount DESC) AS rk
            FROM orders)
        SELECT user_id, order_id, amount
        FROM t WHERE rk = 1 ORDER BY user_id""").fetchall()

# TODO 3：算出「按 order_id 顺序的累计金额」
#         输出 order_id, amount, 累计金额，按 order_id 排，只取前 5 条
#         结果存给 rows_cum
rows_cum = cur.execute(
    """SELECT order_id, amount,
            SUM(amount) OVER(ORDER BY order_id)
        FROM orders
        ORDER BY order_id""").fetchall()

# TODO 4：用户 4（刘强）的每一笔订单，和他「上一笔订单」的金额
#         输出 order_id, order_date, amount, 上一笔金额，按日期升序，共 7 行
#         结果存给 rows_lag
rows_lag = cur.execute(
    """SELECT order_id, order_date, amount,
            LAG(amount) OVER (ORDER BY order_date) AS prev_amount
        FROM orders
        WHERE user_id = 4
        ORDER BY order_date""").fetchall()

# TODO 5（不写代码，写在注释里）：
#         ① 为什么窗口函数不能写在 WHERE 里？（提示：跟执行顺序有关）
#         ② 同样一道「每人最高一单」，用 ROW_NUMBER 得 11 行，用 RANK 得 13 行。
#            业务上你会怎么选？为什么？
# 你的答案：WHERE比窗口函数先执行，导致要筛选的窗口函数内的内容在执行时还不存在。我会倾向于RANK，他能更直观的体现两组数据之间的相同之处


# ------------------------------------------------------------
# 第三部分：自检区（不要改）
# ------------------------------------------------------------
print("===== 自检 =====")
print("TODO1 rows_win ->", rows_win)
print("      | 期望 [(1,11,399.0,4898.0,6), (2,4,129.0,2990.0,7), (3,2,477.0,1423.0,5), (4,4,129.0,2990.0,7), (5,11,1497.0,4898.0,6)]")
print()
print("TODO2 rows_top 行数 ->", len(rows_top) if rows_top is not None else None, "| 期望 13（有人并列第一）")
print("      前 3 行 ->", rows_top[:3] if rows_top else None, "| 期望 [(1,33,798.0), (2,3,477.0), (3,17,267.0)]")
print()
print("TODO3 rows_cum ->", rows_cum)
print("      | 期望 [(1,399.0,399.0), (2,129.0,528.0), (3,477.0,1005.0), (4,129.0,1134.0), (5,1497.0,2631.0)]")
print()
print("TODO4 rows_lag 行数 ->", len(rows_lag) if rows_lag is not None else None, "| 期望 7")
print("      前 3 行 ->", rows_lag[:3] if rows_lag else None)
print("      | 期望 [(4,'2024-08-23',129.0,None), (37,'2024-09-13',159.0,129.0), (13,'2024-09-15',259.0,159.0)]")
print()
print("全对的话，窗口函数你就入门了 —— 这是 SQL 面试里最能拉开差距的一类题。")
print("下一课 06：日期与字符串函数 + NULL 处理。")
