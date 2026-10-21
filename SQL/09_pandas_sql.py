# ============================================================
# SQL 09：SQL + pandas 协作 —— 取数和分析各归各位
# 用法：右键 -> Run '09_pandas_sql'
#
# 【本课的核心一句话】
#   SQL 擅长「筛数据、做聚合、把量大的活交给数据库」
#   pandas 擅长「灵活算、透视、画图、导出」
#   真实工作里几乎都是这个顺序：**先用 SQL 把数据捞出来，再用 pandas 在上面做文章。**
#
# 【本课四件事】
#   ① Python 连数据库有三种方式，差别很大（有一个会直接崩）
#   ② pd.read_sql：一行把查询结果变成 DataFrame
#   ③ 同一个分析，用「纯 SQL」和「SQL + pandas」各做一遍，结果必须一致
#   ④ df.to_sql：把 pandas 的结果写回数据库
#
# 【新词】
#   read_sql / to_sql / SQLAlchemy engine / dtypes / to_period / pct_change
# ============================================================

import sqlite3
import warnings
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
import pymysql
from sqlalchemy import create_engine

from dbconfig import CHARSET, HOST, PASSWORD, PORT, USER

HERE = Path(__file__).parent


# ------------------------------------------------------------
# 第 0 步：三种连接方式，差别很大（先看清，别踩坑）
# ------------------------------------------------------------
print("=== 0. 三种连接方式 ===")
print("   ① sqlite3 连接        -> read_sql ✅   to_sql ✅   （pandas 官方支持）")
print("   ② pymysql 裸连接      -> read_sql ⚠️可用但报警告 / to_sql ❌ 直接报错")
print("   ③ SQLAlchemy engine   -> read_sql ✅   to_sql ✅   无警告（推荐）")
print()

# 我们用第 ③ 种。这一行字符串有个固定格式，拆开看：
#   mysql+pymysql://   -> 用什么数据库 + 用什么驱动
#   root:密码@         -> 用户名:密码
#   localhost:3306     -> 主机:端口
#   /practice          -> 库名
#   ?charset=utf8mb4   -> 连接参数
#
# quote_plus 是给密码做 URL 转义：如果密码里有 @ # % 这类字符，
# 不转义会把连接串拆错。养成习惯总没错。
engine = create_engine(
    f"mysql+pymysql://{USER}:{quote_plus(PASSWORD)}@{HOST}:{PORT}/practice?charset={CHARSET}"
)
print("   连接串（密码已打码）:", engine.url.render_as_string(hide_password=True))
print()


# -----------------------------------------------------------.-
# 第 1 步：read_sql —— 一行把查询结果变成 DataFrame
# ------------------------------------------------------------
print("=== 1. pd.read_sql：SQL 进去，DataFrame 出来 ===")
df = pd.read_sql("SELECT * FROM orders LIMIT 3", engine)
print(df.to_string(index=False))
print()

# 【坑①】列的类型和你在 MySQL 里看到的不一样，必须知道：
#   DECIMAL(10,2)  ->  float64        （pandas 把 Decimal 转成 float，会丢精度）
#   DATE           ->  object         （里面装的是 datetime.date 对象，不是 pandas 的日期）
#   VARCHAR        ->  str            （pandas 3.0 起，字符串默认是 str 类型）
print("   dtypes 长这样：")
print("  ", df.dtypes.to_string().replace("\n", "\n   "))
print("   ⚠️ order_date 是 object，不是日期类型 —— 所以后面要 pd.to_datetime 转一下")
print()


# ------------------------------------------------------------
# 第 2 步：参数化查询（别用字符串拼 SQL）
# ------------------------------------------------------------
print("=== 2. 参数化：params 传字典，防止 SQL 注入 ===")
# 不要写 f"WHERE user_id = {uid}"（拼接），要写占位符 + params。
# SQLAlchemy 的占位符是 %(名字)s —— 和 pymysql 的 %s 又不一样，注意。
df_u4 = pd.read_sql(
    "SELECT order_id, amount FROM orders WHERE user_id = %(uid)s ORDER BY order_id",
    engine,
    params={"uid": 4},
)
print("   用户 4 的订单：", df_u4["order_id"].tolist())
print("   总额：", round(df_u4["amount"].sum(), 2))
print()


# ------------------------------------------------------------
# 第 3 步：同一个分析，两条路做一遍
# ------------------------------------------------------------
print("=== 3. 月度 GMV + 环比：纯 SQL vs SQL+pandas ===")

# ---------- 路 A：全部交给 SQL ----------
# 你在 08 课已经会了：DATE_FORMAT 取月份，LAG 取上一行算环比。
#
# 【坑⓪ 这个最阴，先看】注意下面把 '%Y-%m' 写成了 '%%Y-%%m' —— 两个百分号。
#   为什么？因为 SQL 字符串经过 SQLAlchemy/pymysql 时，驱动会用 Python 的
#   `查询 % 参数` 做占位符替换。你写的单个 % 会被当成格式化符号，
#   于是报错：ValueError: unsupported format character 'Y' (0x59)
#   规则：**用 SQLAlchemy / pd.read_sql 执行带 % 的 SQL 时，% 要写两遍**。
#   （08 课用裸 pymysql 游标且不传参数，所以单个 % 没事 —— 又是"看起来一样"的差异）
sql = """
    WITH t AS (
        SELECT DATE_FORMAT(order_date, '%%Y-%%m') AS ym, SUM(amount) AS gmv
        FROM orders
        WHERE status IN ('paid', 'pending')
        GROUP BY ym
    )
    SELECT ym, gmv,
           ROUND((gmv - LAG(gmv) OVER (ORDER BY ym)) * 100.0
                 / LAG(gmv) OVER (ORDER BY ym), 1) AS mom
    FROM t
    ORDER BY ym
"""
mom_sql = pd.read_sql(sql, engine)
print("   路 A（纯 SQL）：")
print("  ", mom_sql.to_string(index=False).replace("\n", "\n   "))
print()

# ---------- 路 B：SQL 只负责取明细，计算交给 pandas ----------
# 注意：这里 SQL 只写了 SELECT *，一行聚合都没做。
df_all = pd.read_sql("SELECT * FROM orders", engine)

# 【坑②】日期要先转成 pandas 的日期类型，才能按时间分组 / 做时间运算
df_all["order_date"] = pd.to_datetime(df_all["order_date"])

# 筛选：有效订单
valid = df_all[df_all["status"].isin(["paid", "pending"])]

# 按「月」分组求和。dt.to_period("M") 把日期变成「2024-07」这样的月粒度
gmv_pd = valid.groupby(valid["order_date"].dt.to_period("M"))["amount"].sum()

# 环比：pct_change() 就是「这一行比上一行涨了百分之几」，一行搞定
# （SQL 里得写 LAG + 两次除法，pandas 只要一个函数 —— 这就是"灵活")
mom_pd = (gmv_pd.pct_change() * 100).round(1)

print("   路 B（pandas）：")
print("     gmv:", [round(v, 2) for v in gmv_pd.tolist()])
print("     环比:", mom_pd.tolist())
print("   -> 第一行的环比是 NaN（没有上个月可对比），和 SQL 的 NULL 是一个意思")
print()

# ---------- 对账：两条路的结果必须一样 ----------
print("=== 4. 对账（这是本课最重要的动作）===")
gmv_sql = mom_sql["gmv"].astype(float).tolist()
gmv_pd_list = [round(v, 2) for v in gmv_pd.tolist()]
print("   GMV 一致吗：", gmv_sql == gmv_pd_list)
# 环比那份，SQL 的第一行是 None，pandas 的第一行是 NaN，比较时要处理
mom_sql_list = [None if pd.isna(v) else float(v) for v in mom_sql["mom"]]
mom_pd_list = [None if pd.isna(v) else float(v) for v in mom_pd.tolist()]
print("   环比一致吗：", mom_sql_list == mom_pd_list)
print("   -> 两条路都对，才说明你两边都没写错。做不到一致就是有 bug。")
print()


# ------------------------------------------------------------
# 第 5 步：to_sql —— 把 pandas 的结果写回数据库
# ------------------------------------------------------------
print("=== 5. df.to_sql：DataFrame 写回 MySQL ===")
# if_exists 三个取值：
#   "fail"    -> 表存在就报错（默认）
#   "replace" -> 删掉重建
#   "append"  -> 追加数据
out = pd.DataFrame({
    "ym": [str(p) for p in gmv_pd.index],   # Period 转成 "2024-07" 这样的字符串
    "gmv": gmv_pd.values,
    "mom_pct": mom_pd.values,               # NaN 会被写成 NULL
})
# index=False：不要把 DataFrame 的行号（0,1,2...）也写成数据库的一列 —— 这是最常见的多余列
out.to_sql("monthly_gmv", engine, if_exists="replace", index=False)

back = pd.read_sql("SELECT * FROM monthly_gmv ORDER BY ym", engine)
print("   写回再读回：")
print("  ", back.to_string(index=False).replace("\n", "\n   "))
print("   -> 这就是「结果落表」：分析结果存进数据库，别人（或报表工具）就能直接用。")
print()


# ------------------------------------------------------------
# 第 6 步：什么时候用 SQL、什么时候用 pandas
# ------------------------------------------------------------
print("=== 6. 分工判断表 ===")
print("   数据量很大，只想要其中一部分          -> SQL（WHERE 在数据库里筛，别全捞回来）")
print("   分组聚合、排名、画窗口                -> 都行，SQL 更省内存")
print("   要算「买了 A 又买了 B」的交叉分析      -> pandas 更灵活（pivot / merge）")
print("   要画图、导出 Excel、做机器学习        -> 只能 pandas")
print("   要定期跑、结果落表给业务用            -> SQL 写死，pandas 只做校验")
print()
print("   经验法则：**能用 SQL 筛掉的，别捞进 pandas 再筛。**")
print("   十万行以内随你怎么写都行；上百万行时，这一条就是性能的分水岭。")
print()


# ------------------------------------------------------------
# 第二部分：过关任务（在这里作答）
# ------------------------------------------------------------

# TODO 1【读全表】：把 orders 全表读成 DataFrame，存给 df_orders
#         然后把 order_date 转成 pandas 的日期类型（pd.to_datetime）
#         要求：读完之后 df_orders["order_date"].dtype 应该是 datetime64 类型
df_orders = pd.read_sql("SELECT * FROM orders", engine)
df_orders["order_date"] = pd.to_datetime(df_orders["order_date"])
# TODO 2【用 pandas 算月度 GMV】：只算有效订单（paid / pending）
#         按「月」分组求和，结果存给 gmv_pd
#         要求：index 是月（用 dt.to_period("M")），值是金额
#         提示：先筛 valid，再 groupby
valid = df_orders[df_orders.status.isin(["paid", "pending"])]
gmv_pd = valid.groupby(valid["order_date"].dt.to_period("M"))["amount"].sum()
# TODO 3【用 pandas 算环比】：在上一步基础上算百分比环比，保留 1 位小数
#         结果存给 mom_pd（第一行会是 NaN，正常）
#         提示：一个 pct_change() 就够
mom_pd = (gmv_pd.pct_change() *100).round(1)

# TODO 4【用纯 SQL 算一遍并对账】：
#         - 用一条 SQL（WITH + LAG）算出 ym / gmv / 环比，存给 mom_sql（DataFrame）
#         - 然后比较两边的 gmv 是否完全一致，结果存给 same（True / False）
#         提示：DataFrame 的列可以用 mom_sql["gmv"] 取出来
mom_sql = pd.read_sql(
    """WITH t AS (SELECT SUM(amount) AS gmv , DATE_FORMAT(order_date, '%%Y-%%m') AS ym
                    FROM orders
                    WHERE status IN ('paid' , 'pending')
                    GROUP BY ym)
    SELECT ym, gmv, ROUND((gmv - LAG(gmv) OVER(ORDER BY ym)) * 100.0 / LAG(gmv) OVER(ORDER BY ym), 1)
    FROM t
    ORDER BY ym""", engine)

same = gmv_pd.round(2).tolist() == mom_sql["gmv"].astype(float).round(2).tolist()

# TODO 5【结果落表】：把 gmv_pd 和 mom_pd 拼成一个 DataFrame（三列：ym / gmv / mom_pct），
#         用 to_sql 写进 MySQL 的 monthly_gmv 表（存在就替换），
#         再把表读回来存给 back_rows（DataFrame）
#         提示：Period 索引转字符串用 str(p)
out = pd.DataFrame({
    "ym" : [str(p) for p in gmv_pd.index],
    "gmv": gmv_pd.values,
    "mom_pct": mom_pd.values
})
out.to_sql("monthly_gmv", engine, if_exists="replace", index=False)
back_rows = pd.read_sql("SELECT * FROM monthly_gmv ORDER BY ym", engine)

# TODO 6（不写代码，写在注释里）：
#         举两个你自己的例子：什么任务你会用 SQL 做，什么任务你会用 pandas 做？
# 你的答案：取数，筛选和需要在业务中使用的数据用sql，计算，训练等用pandas做


# ------------------------------------------------------------
# 第三部分：自检区（不要改）
# ------------------------------------------------------------
print("===== 自检 =====")
print("TODO1 df_orders 形状 ->", None if df_orders is None else df_orders.shape, "| 期望 (40, 7)")
print("      order_date 的 dtype ->", None if df_orders is None else df_orders["order_date"].dtype,
      "| 期望 datetime64[...]（不是 object 就对了）")
print()
print("TODO2 gmv_pd ->", None if gmv_pd is None else [(str(i), round(float(v), 2)) for i, v in gmv_pd.items()])
print("      | 期望 [(2024-07, 1681.0), (2024-08, 3182.0), (2024-09, 5174.0), (2024-10, 1497.0), (2024-11, 1256.0), (2024-12, 1132.0)]")
print()
print("TODO3 mom_pd ->", None if mom_pd is None else mom_pd.tolist())
print("      | 期望 [NaN, 89.3, 62.6, -71.1, -16.1, -9.9]")
print()
print("TODO4 mom_sql 行数 ->", None if mom_sql is None else len(mom_sql), "| 期望 6")
print("TODO4 same（两条路一致吗）->", same, "| 期望 True")
print()
print("TODO5 back_rows 行数 ->", None if back_rows is None else len(back_rows), "| 期望 6")
print("      back_rows ->")
if back_rows is not None:
    print(back_rows.to_string(index=False))
print()
print("全对的话，你的 Python 侧已经能「取数 -> 分析 -> 落表」走完一整圈了。")
print("这正是数据岗日常工作的最小闭环。")
