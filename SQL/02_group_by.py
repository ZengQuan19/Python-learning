# ============================================================
# SQL 02：聚合与分组 —— 从「取数」升级到「统计」
# 用法：右键 -> Run '02_group_by'
# 数据库：practice.db（同目录）
#
# 【本课两件事】
#   ① 聚合函数：把「很多行」压成「一个数字」
#        COUNT 数个数 / SUM 求和 / AVG 平均 / MIN 最小 / MAX 最大
#   ② GROUP BY：先分组，再在每一组里各算一次聚合
#        再配一个 HAVING，用来筛「组」（不是筛行）
#
# 【面试频率 ★★★★★】
#   「每个用户的订单总额」「每种状态的平均金额」「订单数超过 5 的用户」
#   —— 这类题就是本课内容，几乎每场数据岗面试都会考。
#
# 【本课新词】
#   聚合函数 / 分组 / HAVING / NULL 会被聚合函数跳过
# ============================================================

import sqlite3
from pathlib import Path

DB = Path(__file__).with_name("practice.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()


# ------------------------------------------------------------
# 第一部分：热身（不用改，直接运行）
# ------------------------------------------------------------

# --- 1. 五个聚合函数，一次看全 ---
print("=== 1. 五个聚合函数 ===")
row = cur.execute(
    "SELECT COUNT(*), SUM(amount), AVG(amount), MIN(amount), MAX(amount) FROM orders"
).fetchone()
print("结果：", row)
print("   -> 注意：结果只有一行！40 笔订单被压成了 5 个数字。")
print("      单行的结果用 fetchone() 取，别用 fetchall() 再 [0]，那样容易忘。")
#       ⚠️ 【一行】和【多行】是两条完全不同的路，混了就报错：
#            fetchone()  ->  一行，得到一个元组      ->  直接解包：a, b = row
#            fetchall()  ->  多行，得到元组的列表    ->  才需要 for：for a, b in rows
#          「一行」外面再套 for，等于让 Python 把一个数字拆成两个名字，
#          会报：TypeError: cannot unpack non-iterable int object
#          判断方法就一句：print(type(结果)) —— tuple 是一行，list 是多行。
print(f"      COUNT(*) = {row[0]} 笔订单")
print(f"      SUM      = {row[1]} 总金额")
print(f"      AVG      = {row[2]:.2f} 平均每笔")
print(f"      MIN/MAX  = {row[3]} / {row[4]}")
print()

# --- 2. 真正的坑：COUNT(*) 和 COUNT(列) 不是一回事 ---
print("=== 2. COUNT(*) vs COUNT(列)：NULL 会被跳过 ===")
# 造一张只有 3 行的小表来看这件事，数据一目了然
cur.execute("CREATE TEMP TABLE demo_num (v)")
cur.executemany("INSERT INTO demo_num VALUES (?)", [(None,), (10,), (20,)])
d = cur.execute("SELECT COUNT(*), COUNT(v), SUM(v), AVG(v) FROM demo_num").fetchone()
print("表里 3 个值：NULL、10、20")
print(f"   COUNT(*)  = {d[0]}   <- 数『行数』，NULL 也算一行")
print(f"   COUNT(v)  = {d[1]}   <- 数『非空的值』，NULL 被跳过")
print(f"   SUM(v)    = {d[2]}   <- NULL 不参与计算")
print(f"   AVG(v)    = {d[3]}   <- 30 / 2 = 15，不是 30 / 3 = 10")
print()
print("   ⚠️ 这是最阴的一个陷阱：AVG 的分母是『非空个数』，不是行数。")
print("      你以为的平均，和数据库给你的平均，可能不是同一个数 —— 还不报错。")
print("      结论：只要数据可能有空值，就同时写出 COUNT(*) 和 COUNT(该列) 对一下。")
print()

# --- 3. GROUP BY：先分组，再各组算一次 ---
print("=== 3. GROUP BY：先分组，再聚合 ===")
rows = cur.execute(
    "SELECT status, COUNT(*), SUM(amount) FROM orders GROUP BY status"
).fetchall()
print("读法：把 orders 按 status 分成几堆，每一堆各算一次 COUNT 和 SUM")
for status, n, total in rows:      # 这行是「元组解包」：三个名字一次接住三个值
    print(f"   {status:<10} {n:>3} 笔   {total:>10} 元")
print()
print("   -> 返回几行，取决于分了几组：4 种状态就返回 4 行。")
print("      ⚠️ 自查小技巧：写 GROUP BY 之前先想『应该有几行』，跑完对一下。")
print("         行数不对，说明你的分组列选错了。")
print()

# --- 4. GROUP BY 的规矩（跨数据库会翻车）---
print("=== 4. SELECT 里不要出现「既没分组、也没聚合」的裸列 ===")
bad = cur.execute("SELECT status, order_id, COUNT(*) FROM orders GROUP BY status").fetchall()
print("   ", bad)
print("   -> SQLite 没报错，但它随便从每组里挑了一个 order_id 给你，这列毫无意义。")
print("      MySQL（开着 ONLY_FULL_GROUP_BY，也就是默认状态）会直接报错：")
print("      Expression #2 of SELECT list is not in GROUP BY clause ...")
print("      规矩：SELECT 后面只允许两类东西 —— ①分组列 ②聚合函数。")
print()

# --- 5. WHERE vs HAVING（面试必考）---
print("=== 5. WHERE 筛行，HAVING 筛组 ===")
print("这两条 SQL 长得很像，结果不一样：")
a = cur.execute("SELECT status, COUNT(*) FROM orders WHERE amount > 200 GROUP BY status").fetchall()
print("   WHERE  amount > 200 再分组：", a)
b = cur.execute("SELECT status, COUNT(*) FROM orders GROUP BY status HAVING COUNT(*) > 5").fetchall()
print("   GROUP BY 之后 HAVING COUNT(*) > 5：", b)
print()
print("   区别在哪：")
print("     WHERE  = 分组之前，先把不合格的『行』扔掉   -> 影响参与统计的数据")
print("     HAVING = 分组之后，再把不合格的『组』扔掉   -> 不影响统计结果，只筛组")
print("   ⚠️ WHERE 里不能写聚合函数（COUNT/SUM...），因为那时还没分组。")
print("      想按『聚合出来的结果』筛选，只能用 HAVING。")
print()
print("   完整的执行顺序（背下来，面试常问）：")
print("     FROM -> WHERE -> GROUP BY -> HAVING -> SELECT -> ORDER BY -> LIMIT")
print()

# --- 6. 把结果读成表 ---
print("=== 6. 组合起来：每种状态的订单数、总金额、平均金额 ===")
final = cur.execute(
    """
    SELECT status, COUNT(*) AS n, SUM(amount) AS total, AVG(amount) AS avg_amt
    FROM orders
    GROUP BY status
    ORDER BY total DESC
    """
).fetchall()
print(f"{'状态':<10}{'单数':>6}{'总金额':>12}{'平均':>10}")
for status, n, total, avg_amt in final:
    print(f"{status:<10}{n:>6}{total:>12.0f}{avg_amt:>10.1f}")
print("   -> 三引号 \"\"\"...\"\"\" 可以写多行 SQL，比用加号拼字符串清楚得多。")
print("      AS 是给结果列起别名，只影响显示，不改数据。")
print()

# --- 6.5 花括号里的冒号是干嘛的：f-string 格式说明符 ---
# 上面那行 f"{status:<10}{n:>6}" 里，花括号分两半：
#     冒号【左边】= 要填进去的值（变量名，也可以是表达式）
#     冒号【右边】= 排版规则（占多宽、左对齐还是右对齐、保留几位小数）
#
#   对齐符号：  <  左对齐      >  右对齐      ^  居中
#   数字     ：  占几个字符的宽度（不够就用空格补）
#   其他常用 ：  .2f 保留两位小数   , 千分位   %  百分数   0 补零
#
# 看一眼实际效果，比看规则快：
demo_status, demo_n, demo_total = "paid", 18, 19624.0
print("=== 6.5 f-string 排版速查 ===")
print("左对齐   {:<10} ->", f"[{demo_status:<10}]")
print("右对齐   {:>10} ->", f"[{demo_status:>10}]")
print("居中     {:^10} ->", f"[{demo_status:^10}]")
print("数字宽度 {:>3}  ->", f"[{demo_n:>3}]", " 宽度不够也不会截断：", f"[{1234:>3}]")
print("补零     {:03d} ->", f"[{7:03d}]")
print("自选填充 {:*>8} ->", f"[{'x':*>8}]")
print("两位小数 {:.2f} ->", f"[{3.14159:.2f}]")
print("千分位   {,.0f} ->", f"[{demo_total:,.0f}]")
print("百分数   {:.1%} ->", f"[{0.856:.1%}]")
print("   -> 之前用过的 f\"{row[2]:.2f}\" 里的 .2f，和这里的 <10 是同一个位置的东西。")
print()
print("   ⚠️ 中文对齐陷阱：:<10 数的是【字符个数】，不是屏幕宽度。")
print("      一个汉字占 2 个屏幕宽度，却只算 1 个字符，所以上面表头会歪。")
print(f"      [{'状态':<10}]  <- 看起来比 [{'paid':<10}] 宽")
print("      想让中文表格真正对齐，要么手算宽度，要么交给 pandas / 表格库。")
print()


# ------------------------------------------------------------
# 第二部分：过关任务（在这里作答）
# ------------------------------------------------------------
# 要求：自己敲。写完整个文件跑一次，对照最后的自检区。

# TODO 1：三个数，全部要是「数字」，不能是列表
#         - n_total：orders 表总行数
#         - n_paid ：paid 状态的订单数
#         - sum_paid：paid 状态的金额总和
#         提示：后两个可以用同一条 SQL 一次查出来（一行两列），
#              用 fetchone() 拿到，再用解包接住两个值。
cur.execute("SELECT COUNT(*) FROM orders")
n_total = cur.fetchone()[0]
TEMP = cur.execute("SELECT COUNT(*), SUM(amount) FROM orders WHERE status = 'paid'").fetchone()
n_paid , sum_paid = TEMP

# TODO 2：按 status 分组，得到三列：状态、订单数、总金额，
#         按「总金额」从大到小排。结果存给 rows_status（list）
#         提示：GROUP BY + ORDER BY，注意 ORDER BY 后面写什么。

rows_status = cur.execute("SELECT status , COUNT(*) , SUM(amount) FROM orders GROUP BY status ORDER BY SUM(amount) DESC").fetchall()

# TODO 3：每个用户有多少笔订单，只保留「订单数 >= 5」的用户，
#         按订单数从大到小排。结果存给 busy_users（list）
#         提示：这就是 HAVING 的用武之地。先想清楚 should be 几行。
#         ⚠️ 分组题第一步永远是定「粒度」：这次的结果，一行代表谁？
#            粒度定了，再拿这句话去筛每一列：
#              「我 SELECT 的这一列，在这一行里是不是只有一个值？」
#            只有【分组列】和【聚合结果】满足这句话。
#            其他裸列（比如 order_id）一个用户对应好多笔订单，塞进来就是废数据
#            —— 这正是第 4 节讲的那个「裸列」坑，只是换了个地方出现。
cur.execute("SELECT user_id , COUNT(*) FROM orders GROUP BY user_id HAVING COUNT(*) >= 5 ORDER BY COUNT(*) DESC")
busy_users = cur.fetchall()

# TODO 4：在 users 表上，用一条 SQL 同时算出
#           cnt_all  = COUNT(*)
#           cnt_city = COUNT(city)
#         再用 Python 算出 diff = cnt_all - cnt_city
#         ⚠️ 最后写一行注释回答：为什么这两个数不相等？
cur.execute("SELECT COUNT(*) , COUNT(city) FROM users")
cnt_all, cnt_city = cur.fetchone()
diff = cnt_all - cnt_city
print(cur.execute("SELECT DISTINCT city FROM users").fetchall())
# 你的解释：
#有人不填city项，而*会选择包括NULL在内的进行操作，但city这个选择器不会
# TODO 5（不写代码，写在注释里）：
#         如果要「只统计 paid 状态，再找出订单数 >= 5 的用户」，
#         WHERE 和 HAVING 各该放什么？为什么不能把 paid 写进 HAVING？
# 你的答案：WHERE填status = paid，HAVING填COUNT(*) >= 5
#把paid写进HAVING里会导致先找出订单数满足的用户，再统计paid订单数，会导致出现paid订单数低于5的以外值


# ------------------------------------------------------------
# 第三部分：自检区（不要改）
# ------------------------------------------------------------
print("===== 自检 =====")
print("TODO1 n_total  ->", n_total, "| 期望 40（数字，不是 [40]）")
print("TODO1 n_paid   ->", n_paid, "| 期望 18")
print("TODO1 sum_paid ->", sum_paid, "| 期望 11417.0")
print("      自检：n_total 的类型 ->", type(n_total).__name__, "| 期望 int")
print()
print("TODO2 rows_status 行数 ->", len(rows_status) if rows_status is not None else None, "| 期望 4")
print("      ->", rows_status)
print("      | 期望顺序：paid(18,11417.0) -> cancelled(7,3271.0) -> pending(9,2505.0) -> refunded(6,2431.0)")
print()
print("TODO3 busy_users ->", busy_users, "| 期望 [(4, 7), (11, 6), (2, 5)]")
print()
print("TODO4 cnt_all  ->", cnt_all, "| 期望 12")
print("TODO4 cnt_city ->", cnt_city, "| 期望 11")
print("TODO4 diff     ->", diff, "| 期望 1")
print()
print("全对的话，你已经会『分组统计』了 —— 这是 SQL 面试出现最多的一类题。")
print("下一课 03：多表 JOIN，把 orders 和 users 拼起来看。")
