# ============================================================
# Agent/db.py —— 数据层：只负责"连库 + 查数据"，不碰网页
#
# 怎么跑（不需要开 Flask）：
#   1. 右键本文件 -> Run 'db'
#   2. 或终端执行：.venv\Scripts\python.exe Agent\db.py
#
# 为什么单独拆一个文件：
#   app.py 是"网页"，db.py 是"数据"。网页代码不该关心密码、端口、游标。
#   v2 接 LLM、v3 加工具调用时都会直接 import 这里的函数，不用复制连接代码。
# ============================================================

import sys
from pathlib import Path

import pymysql

# --- 让本文件能找到 SQL/dbconfig.py ---
# 密码只存一份：SQL/dbconfig.py（已被 .gitignore 排除，不进仓库）。
# 我们不复制、不移动它，只是把它所在目录加进 Python 的模块搜索路径 sys.path，
# 这样下面的 import dbconfig 就能找到。
SQL_DIR = Path(__file__).resolve().parent.parent / "SQL"
if str(SQL_DIR) not in sys.path:
    sys.path.insert(0, str(SQL_DIR))

# 注意：这行必须放在上面 sys.path 设置之后，不是写错了顺序。
import dbconfig


# ------------------------------------------------------------
# ① 可运行的热身示例（先跑通，先别改）
# ------------------------------------------------------------
def get_conn():
    """返回一条连到 practice 库的连接。

    和你在 SQL/08_mysql.py 里写过的相比，只多了两个参数：
      database="practice"      -> 连上后直接 USE practice，不用再单独执行 USE
      cursorclass=DictCursor   -> fetchall() 返回 dict 而不是 tuple，键就是列名
                                  （下一版拼 JSON 特别方便，现在先体会一下）
    """
    return pymysql.connect(
        host=dbconfig.HOST,
        port=dbconfig.PORT,
        user=dbconfig.USER,
        password=dbconfig.PASSWORD,
        charset=dbconfig.CHARSET,
        database="practice",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )


# ------------------------------------------------------------
# ② TODO 区（留 None，你自己填）
# ------------------------------------------------------------
# 任务：写 top_user()，查出"花钱最多的用户"。
#
#   【先定口径】订单有 4 种状态：paid / pending / cancelled / refunded。
#   "花钱最多"到底算哪些状态？不同口径结果不一样，这是数据分析里最先要问清的事。
#   本题口径：只算 status = 'paid'（已支付 = 真金白银付出去了）。
#
#   返回值固定成这个形状：
#     {"user_id": 11, "name": "孙悦", "city": "深圳", "total": 4112.0, "orders": 4}
#   五个键含义：用户 id / 姓名 / 城市 / 已支付总额 / 已支付订单数
#
#   实现要求：
#     1. users JOIN orders（你 JOIN 很熟，这步不难）
#     2. 用 WHERE 只留 paid
#     3. 按总额降序，只取第一行（LIMIT 1）
#     4. total 用 float(...) 转一下 —— MySQL 的 SUM 返回 Decimal，
#        下一步 Flask 把它转 JSON 会报 "Object of type Decimal is not JSON serializable"
#     5. 查不到时返回 None（想想：什么情况下会查不到？）
#
#   写完后运行本文件，看 ③ 区打印的 实际 vs 期望。


def top_user():
    # TODO: 在这里写 SQL，然后 return dict
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """SELECT u.user_id, u.name, u.city, SUM(o.amount) AS total, COUNT(*) AS orders
           FROM users u
        LEFT JOIN orders o ON o.user_id = u.user_id
        WHERE o.status = 'paid'
        GROUP BY u.user_id
        ORDER BY total DESC
        LIMIT 1"""
    )
    result = cur.fetchone()
    result['total'] = float(result['total'])
    return result


# ------------------------------------------------------------
# ③ 自检区（不用改）
# ------------------------------------------------------------
EXPECTED = {
    "user_id": 11,
    "name": "孙悦",
    "city": "深圳",
    "total": 4112.0,
    "orders": 4,
}


def selfcheck():
    print("===== 自检 =====")

    conn = get_conn()
    # 注意：因为用了 DictCursor，fetchone() 返回的是 dict，不能直接拆包
    with conn.cursor() as cur:
        cur.execute("SELECT VERSION() AS ver, DATABASE() AS db")
        row = cur.fetchone()
    conn.close()
    print("① 连接 OK：MySQL", row["ver"], "| 当前库:", row["db"], "| 期望 practice")

    result = top_user()
    print("② top_user() 实际:", result)
    print("   期望             :", EXPECTED)

    if not result:
        print("③ 判定: FAIL —— 还没返回数据，去 ② 区写 TODO")
        return

    total = float(result.get("total", 0))
    ok = (
        result.get("user_id") == EXPECTED["user_id"]
        and result.get("name") == EXPECTED["name"]
        and abs(total - EXPECTED["total"]) < 0.01
        and result.get("orders") == EXPECTED["orders"]
    )
    print("③ 判定:", "PASS" if ok else "FAIL")

    if abs(total - 4898.0) < 0.01:
        print("   提示：4898 是【所有状态】订单的总额。")
        print("        本题口径只算 paid，所以 SQL 里要有 WHERE status = 'paid'。")


if __name__ == "__main__":
    selfcheck()
