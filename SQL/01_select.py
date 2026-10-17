# ============================================================
# SQL 01：第一次查询 —— 学会向数据库提问
# 用法：右键 -> Run '01_select'
# 数据库：practice.db（同目录；玩坏了就跑一次 make_db.py 复原）
#
# 【为什么 SQL 排第一优先级】
#   数据 / 开发岗的笔试面试，第一关就是 SQL。它两周能入门、能立刻做题，
#   是所有技能里「价值 ÷ 成本」最高的一项 —— 所以它从今天开始，不是以后。
#
# 【本课只学一件事】用 SELECT 把数据问出来。一条查询永远由这 5 块拼成：
#   SELECT 要哪些列  FROM 哪张表  WHERE 什么条件  ORDER BY 怎么排  LIMIT 要几条
#   只有 SELECT 和 FROM 是必须的，其余按需要加。
#
# 【顺带练的语言功能】
#   ① Python 自带 sqlite3 —— 不用装数据库、不用配服务，import 就能用
#   ② SQL 语句是写在「字符串」里的，所以引号规则要搞清楚
#   ③ 查询结果先是 tuple 的 list，再交给 pandas 变成 DataFrame（衔接你的强项）
#
# 【如果卡在 connect / cursor / execute 上】
#   先读第 0 步那一大段注释（图书馆比喻），再跑 1.5 节实验。
#   那两处专门讲它们，看懂再往下。
# ============================================================

import sqlite3
from pathlib import Path
import pandas as pd


# ------------------------------------------------------------
# 第 0 步：连上数据库
# ------------------------------------------------------------
# 为什么不用 sqlite3.connect("practice.db")？
#   相对路径是相对「运行时的工作目录」，不是你想象的「这个文件所在的目录」。
#   PyCharm 默认把工作目录设成项目根（Python\），那样就找不到 SQL\practice.db 了。
#   __file__ 是「本文件自己的路径」，用它推出同目录下的 db，永远不会错。
#   ⚠️ 这个坑以后写任何脚本都会遇到，记住这个写法。
DB = Path(__file__).with_name("practice.db")

# ============================================================
# 下面三行是「连上数据库」的全部机关，一行一行拆开看
# ============================================================
#
#   第 1 行  conn = sqlite3.connect(DB)
#            建立「连接」。conn = connection（连接）。
#            相当于：你走进图书馆，门开了、灯亮了，可以开始办事了。
#            注意：此刻你还没拿到任何数据。
#
#   第 2 行  cur = conn.cursor()
#            cursor 直译是「光标 / 游标」。cur = cursor。
#            这是在连接上开出的「一只取数的手」。
#            为什么要多这一层？因为一个连接可以同时开好几个游标，
#            就像你在图书馆里同时借好几本书，每只手各拿一摞、互不干扰。
#            （后台同时跑多个查询时会用到；现在知道「有这回事」就够）
#
#   第 3 步  cur.execute("SELECT ...")
#            把一条 SQL 交给数据库去执行。
#            ⚠️ 关键：execute 只是「把要求提出来」，结果还躺在数据库那边，
#               必须再 fetch 一次，才是「把结果拿到自己手里」。
#               忘了 fetch，你会误以为查询什么都没返回。
#
#   cur.fetchall()  → 结果全部取回：一个 list，一行一个 tuple
#   cur.fetchone()  → 只取一行；每调用一次，游标往前挪一行
#
# 图书馆版总结（记住这张图就够了）：
#   connect()  = 走进图书馆
#   cursor()   = 伸出手去取数
#   execute()  = 告诉管理员「我要哪本书」
#   fetchXXX() = 把书真正拿到手上
#
# ⚠️ 另一个静默陷阱：连接一个「不存在的文件」不会报错，
#    SQLite 会直接帮你新建一个空库。所以文件名拼错时，
#    你看到的报错会是 no such table，而不是「文件不存在」，
#    很容易误以为表被删了。遇到 no such table，先 print(DB) 看连的是哪个文件。
conn = sqlite3.connect(DB)
cur = conn.cursor()


# ------------------------------------------------------------
# 第一部分：热身（不用改，直接运行）
# ------------------------------------------------------------

# --- 1. 先看库里有什么表 ---
print("=== 1. 先看这个库里有什么表 ===")
print(cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
print("   -> sqlite_master 是 SQLite 自带的『目录表』，相当于书的目录。")
print("   -> 这跟你在 01_first_request 里先 json.dumps 看结构是同一个习惯：")
print("      先看结构，再写查询。别猜表名和列名。")
print()

# --- 1.2 一张表有哪些「列」：筛选之前必须先做这一步 ---
print("=== 1.2 怎么看一张表有哪些列 ===")

print("方法一：PRAGMA table_info(表名)")
for col in cur.execute("PRAGMA table_info(orders)").fetchall():
    print("   ", col)
print("   -> SQLite 查表结构的官方方式，一次给你全部列名和类型。")
print("      每行 6 个字段：(编号, 列名, 类型, 是否非空, 默认值, 是否主键)")
print("      （MySQL 里对应的是 DESCRIBE 表名 或 SHOW COLUMNS FROM 表名，面试会问）")
print()

print("方法二：游标的 .description —— 查询执行完，列名就挂在游标上")
cur.execute("SELECT * FROM orders LIMIT 1")
print("   列名：", [d[0] for d in cur.description])
print("   -> description 是个 list，每个元素是「一个列说明」的元组，第 0 位才是列名。")
print("      所以要用列表推导式 d[0] 把它挑出来。")
print()

print("方法三：交给 pandas（你的强项）")
df_cols = pd.read_sql("SELECT * FROM orders LIMIT 1", conn)
print("   列名：", df_cols.columns.tolist())
print("   -> 三招选一个记住就行，目的都是：别猜列名。")
print()

print("但读列名只是第一步。要写 WHERE，你还得知道这一列里的『值』长什么样：")
print("   举例（看 products 的 category 列有哪些取值）：")
print("   ", cur.execute("SELECT DISTINCT category FROM products").fetchall())
print("   -> DISTINCT 是去重：把这一列出现过的所有不同取值列给你。")
print("   -> 为什么必须查值、不能猜：真实数据里可能是 paid / Paid / PAID / 已支付，")
print("      你猜一个写法，条件对不上，SQL 不报错，只是默默返回 0 行。")
print("      ⚠️ 这是最典型的静默失败：没报错，但结果是空的。")
print("   -> 所以筛选前固定动作：① 查列名  ② 查这列有哪些值  ③ 再写 WHERE")
print("      现在，你自己去 orders 表上做这两个动作。")
print()

# --- 1.5 游标到底「游」在哪：亲眼看一下 fetchone 怎么走 ---
print("=== 1.5 游标「游」在哪 ===")

# 先把下面这条 SQL 的后半段拆开（最容易卡住的就是这里）：
#   ORDER BY age DESC
#     ORDER BY = 「按什么排」，后面跟用来排序的列名，这里是 age
#     DESC     = descending（降序），数字从大到小：52 -> 45 -> 41 ...
#     默认是 ASC = ascending（升序），从小到大；升序时 ASC 可以不写
#   整句读作：「从 users 表里取出 name 和 age 两列，按 age 从大到小排」
#
#   ⚠️ 不写 ORDER BY 时，数据库返回的顺序是「不保证」的：
#      今天看着像按 id 排，换个库、加个索引就可能变。
#      需要顺序就显式写 ORDER BY —— 又是典型的静默陷阱。
res = cur.execute("SELECT name, age FROM users ORDER BY age DESC")
print("cur.execute(...) 的返回值 res 是什么：", type(res))
print("res 和 cur 是同一个对象吗：", res is cur)
print("   -> execute 返回的就是这个游标本身。")
print("      所以 cur.execute(...).fetchall() 这种连写才成立：先执行，立刻取结果。")
print()
print("第一次 fetchone()：", res.fetchone())
print("第二次 fetchone()：", res.fetchone())
print("第三次 fetchone()：", res.fetchone())
print("   -> 每调用一次，游标往前挪一格。这就是「游标 / 光标」这个名字的由来。")
print("      它只进不退：拿走的那一行不会再给你第二遍。")
print()
left = res.fetchall()
print("剩下的全拿走 fetchall()：", len(left), "行（12 个用户 - 已取走 3 行 = 9）")
print("再 fetchall() 一次：", res.fetchall(), "  <- 空了，游标已经到底")
print()
cur.execute("SELECT name FROM users LIMIT 2")
print("重新 execute 一条新 SQL，游标回到开头：", cur.fetchall())
print("   -> 同一个游标上只保留最近一次查询的结果，之前的结果被丢弃。")
print("      这就是为什么「执行一条、立刻取结果」是最安全的写法。")
print()

# --- 2. 第一次查询：看看 users 表长什么样 ---
print("=== 2. SELECT * FROM users LIMIT 5 ===")
print(cur.execute("SELECT * FROM users LIMIT 5").fetchall())
print("   -> * 表示『所有列』；LIMIT 5 表示『先只给我 5 行』。")
print("      看一张不认识的表，先这样看一眼。")
print()

# --- 3. 只取需要的列 ---
print("=== 3. 只取 name 和 city 两列 ===")
print(cur.execute("SELECT name, city FROM users").fetchall())
print("   -> 列之间用逗号隔开。真做项目时不要动不动 SELECT *：")
print("      只要 2 列却把 20 列都拉回来，是速度和内存的浪费。")
print()

# --- 4. WHERE：按条件过滤 ---
print("=== 4. WHERE 过滤：只要北京的用户 ===")
print(cur.execute("SELECT name, city FROM users WHERE city = '北京'").fetchall())
print("   -> ⚠️ 文字要用单引号包起来：'北京'。不包的话 SQL 会以为那是列名，直接报错。")
print("   -> ⚠️ 相等判断在 SQL 里写一个 =，不是 Python 的 ==。这是最常见的写错。")
print()

# --- 5. ORDER BY + DESC + LIMIT ---
# 这条比 1.5 多了最后那一小截：... ORDER BY age DESC LIMIT 3
#   LIMIT 3 = 排完序之后，只要前 3 行。因为排在前面的是年龄最大的，
#             所以拿到的是「年龄最大的 3 个人」。
#   ⚠️ 执行顺序是：FROM 找表 -> WHERE 过滤 -> ORDER BY 排序 -> LIMIT 截断。
#      LIMIT 永远在排序之后生效，这一点搞反了结果就完全不同。
print("=== 5. 排序取前几名：年龄最大的 3 个人 ===")
print(cur.execute("SELECT name, age FROM users ORDER BY age DESC LIMIT 3").fetchall())
print("   -> 结果：吴磊 52、刘强 45、马丽 41（这正是 age 最大的三个）")
print("   -> ORDER BY 列名 是升序（默认 ASC），DESC 是降序。")
print("   -> 『取 Top N』的标准套路：ORDER BY ... DESC LIMIT N。面试常考。")
print("   -> 把 DESC 去掉或换成 ASC，就变成『年龄最小的 3 个人』：")
print("      SELECT name, age FROM users ORDER BY age LIMIT 3")
print("      （这条我没跑，你自己跑一遍验证——自己验证过的东西才是你的）")
print()

# --- 6. 结果在 Python 里是什么东西 ---
print("=== 6. 查询结果的数据类型 ===")
rows = cur.execute("SELECT name, city FROM users WHERE city = '上海'").fetchall()
print("类型：", type(rows), "| 里面的元素类型：", type(rows[0]))
print("内容：", rows)
print("   -> 是 list 套 tuple：一行一个 tuple，列的顺序跟你 SELECT 的顺序一致。")
print("      tuple 不能改，想要能改的结构就自己转成 list 或 DataFrame。")
print()

# --- 7. 交给 pandas：一行 SQL 直接变 DataFrame ---
print("=== 7. pandas.read_sql：SQL 拿来，DataFrame 出来 ===")
df_bj = pd.read_sql("SELECT name, city, age FROM users WHERE city = '北京'", conn)
print(df_bj)
print("形状：", df_bj.shape)
print("   -> 你的两条技能线在这里接上了：")
print("      SQL 负责『取数和筛选』，pandas 负责『分析和统计』。")
print("      真实工作里绝大多数时候就是这么分工的。")
print()

# --- 8. 四个坑：三个会报错，一个不会（不报错的那个最危险）---
print("=== 8. 四个坑，故意踩给你看 ===")

try:
    cur.execute("SELECT name FROM users WHERE city = 北京").fetchall()
except sqlite3.OperationalError as e:
    print("坑① 文字没加单引号 ->", e)
    print("    报错说『没有名为 北京 的列』，其实你想说的是『值等于北京』。")
    print("    报错里出现 no such column，八成是你把「值」写成了「列名」。")

try:
    cur.execute("SELECT naem FROM users").fetchall()
except sqlite3.OperationalError as e:
    print("坑② 列名拼错 ->", e)
    print("    SQL 不会帮你猜。回去第 1、2 步看列名怎么拼。")

try:
    cur.execute("SELECT name FROM user").fetchall()
except sqlite3.OperationalError as e:
    print("坑③ 表名写错 ->", e)
    print("    遇到这个，回去跑第 1 步，看表名到底叫什么。")

print()
print("坑④ 下面这两个『居然不报错』—— 这才是最危险的一类：")
silent1 = cur.execute("SELECT name, age FROM users WHERE age == 28").fetchall()
print("   age == 28（双等号）->", silent1, "  ← 没报错！")
silent2 = cur.execute('SELECT name, city FROM users WHERE city = "北京"').fetchall()
print('   city = "北京"（双引号）-> 共', len(silent2), "行     ← 也没报错！")
print()
print("   为什么危险：SQLite 比较宽容，帮你把这两个都『圆』过去了，")
print("   但换一个数据库（MySQL / PostgreSQL）就可能直接报错，")
print("   或者把双引号当成『列名』来理解 —— 查询结果悄悄变错，还不提示你。")
print("   这就是静默失败：不报错，但结果是错的。")
print()
print("   两条铁律，现在刻进去：")
print("     ① 文字值永远用单引号 '北京'，不用双引号")
print("     ② 相等判断永远写一个 =，不写 ==")
print()

# 连接先不关，下面 TODO 还要用。
# （正式项目里要么显式 conn.close()，要么用 with 语句，那是后面的事）


# ------------------------------------------------------------
# 第二部分：过关任务（在这里作答）
# ------------------------------------------------------------
# 要求：自己敲，别复制上面的。SQL 是手感活，敲一遍胜过看十遍。
#      写完整个文件跑一次，对照最后的自检区。

# TODO 1：查出所有「上海」的用户，只要 name 和 city 两列
#         - 原始结果（list）存给 sh_rows
#         - 同一份数据用 pandas.read_sql 存给 sh_df
#         提示：先写 SQL 字符串，再调用；两条路用同一个条件。
sh_rows = cur.execute("SELECT name, city FROM users WHERE city ='上海'").fetchall()
sh_df = pd.read_sql("SELECT name, city FROM users WHERE city ='上海'", conn)

# TODO 2：查出所有「金额大于 200 且状态是 paid」的订单，
#         只取 order_id、amount 两列，按金额从大到小排，只要前 5 条
#         结果存给 top5（用 fetchall 拿成 list）
#         提示：两个条件用 AND 连起来，注意 status 是文字。
cur.execute("SELECT * FROM orders LIMIT 1")
print("orders有什么栏目？")
print([d[0] for d in cur.description])
print("status有哪些状态?")
print(cur.execute("SELECT DISTINCT status FROM orders").fetchall())
top5 = cur.execute("SELECT order_id, amount FROM orders WHERE amount > 200 AND status = 'paid' ORDER BY amount DESC LIMIT 5").fetchall()

# TODO 3：orders 表一共有多少行？存给 n_orders（要 int，不是 list）
#         提示：SELECT COUNT(*) FROM ... —— 这个函数正式讲在 02 课，先偷跑一下。
#         拿到的是一个 tuple，取第 0 个元素才是数字。
cur.execute("SELECT COUNT(*) FROM orders")
n_orders = [d[0] for d in cur.fetchall()]

# TODO 4：products 表里最贵的那个产品叫什么？名字存给 priciest（字符串）
#         提示：还是「排序 + 取第一条」那套。
cur.execute("SELECT * FROM products LIMIT 1")
print("product有什么栏目？")
print([d[0] for d in cur.description])
rows = cur.execute("SELECT product_name FROM products ORDER BY price DESC LIMIT 1").fetchall()
print(type(rows),type(rows[0]),type(rows[0][0]))
priciest = rows[0][0]


# ------------------------------------------------------------
# 第三部分：自检区（不要改）
# ------------------------------------------------------------
print("===== 自检 =====")
print("TODO1 sh_rows 行数 ->", len(sh_rows) if sh_rows is not None else None, "| 期望 3")
print("      内容 ->", sh_rows)
print("      | 期望是 王芳 / 陈静 / 郑爽，三个上海用户")
print("TODO1 sh_df 形状   ->", (sh_df.shape if sh_df is not None else None), "| 期望 (3, 2)")
print()
print("TODO2 top5 条数    ->", len(top5) if top5 is not None else None, "| 期望 5")
print("      前两条 ->", top5[:2] if top5 is not None else None)
print("      | 期望第一条 order_id=7、amount=2198.0；第二条 order_id=5、amount=1497.0")
print()
print("TODO3 n_orders     ->", n_orders, "| 期望 40")
print("TODO4 priciest     ->", priciest, "| 期望 显示器")
print()
print("全对的话，你已经会『问数据库要数据』了。")
print("下一课 02：COUNT / SUM / AVG + GROUP BY，从『取数』升级到『统计』。")
