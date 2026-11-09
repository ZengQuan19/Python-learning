# ============================================================
# Agent/qa.py —— 问答编排层：把"一句中文问题"变成"一个答案"
#
# 怎么跑（不用开 Flask）：
#   .venv\Scripts\python.exe Agent\qa.py
#
# 【为什么要单独一层】
#   现在有三个零件，各干各的：
#       llm.ask_sql()   问题 -> SQL
#       db.check_sql()  审核 SQL
#       db.run_select() 执行 SQL -> 数据
#       llm.explain()   问题+SQL+数据 -> 人话解释
#   谁来把它们按顺序串起来、并且在每一步出错时决定"怎么办"？
#   就是这个文件。app.py 只负责"收请求、调这里、渲染页面"，不该塞业务逻辑。
#
#   分层的好处这里能直接看到：
#     - 换模型（llm.py）、换数据库（db.py），这层不用动
#     - v3 加"工具调用"，改的也是这层的"选工具"逻辑
# ============================================================

from db import check_sql, run_select
from llm import ask_sql, explain


# ------------------------------------------------------------
# ① 可运行的热身示例：看一眼每个零件的"返回值形状"
# ------------------------------------------------------------
# 这层不调 API、不连库，只负责"按顺序调用 + 处理异常"。
# 先记住四个零件的返回值：
#     ask_sql(q)       -> {"sql": "...", "raw": "..."}
#     check_sql(sql)   -> (True/False, "原因")
#     run_select(sql)  -> [{"列名": 值, ...}, ...]   （list[dict]）
#     explain(q,sql,rows) -> ("解释文本", usage)


# ------------------------------------------------------------
# ② TODO 区（你自己填）：写 run_question()
# ------------------------------------------------------------
# 契约（返回的 dict 形状固定，页面和自检都按这个取数据）：
#
#   {
#     "question": 用户的问题,
#     "sql":      模型写的 SQL（拿不到就是 None）,
#     "rows":     查询结果 list[dict]，出错时是 None,
#     "error":    出错原因（字符串），一切正常时是 None,
#     "explain":  人话解释，出错时是空字符串 "",
#   }
#
# 为什么要这么设计：**成功和失败用同一个形状返回**，
# 页面就不用写两套逻辑——看 error 有没有值，就知道该显示表格还是显示错误。
#
# 分四步写：
#   第 1 步：问题 -> SQL
#       result = ask_sql(question)
#       sql = result["sql"]
#       ⚠️ ask_sql 会抛异常（key 错了、网络断了、余额不足），
#          所以要用 try/except Exception 包起来，出错就返回 error，别让页面 500。
#       ⚠️ 调用失败时 sql 还不存在，先把 sql = None 准备好。
#
#   第 2 步：审核
#       ok, reason = check_sql(sql)
#       不通过 -> 返回 {"error": f"SQL 未通过安全校验：{reason}", "sql": sql, "rows": None, "explain": ""}
#       页面会把这条错误原样显示给用户（比如模型想写 DELETE 时）。
#
#   第 3 步：执行
#       rows = run_select(sql)
#       run_select 会 raise ValueError（校验失败）或 pymysql 的错（SQL 语法错），
#       同样 try/except，返回 error。
#
#   第 4 步：解释
#       explain_text, usage = explain(question, sql, rows)
#       返回完整 dict。
#       （解释失败也别让整个请求崩，可以降级成 explain=""）
#
# 写完跑 python Agent\qa.py，看 ③ 区输出。


def run_question(question):
    # TODO: 按上面四步实现
    try:
        result = ask_sql(question)
        sql = result["sql"]
    except Exception as e:
        return {"question": question,
                "sql": None,
                "rows":None,
                "error": str(e),
                "explain":""}
    ok, reason = check_sql(sql)
    if not ok:
        return {"question": question,
                "sql": sql,
                "rows":None,
                "error": str(reason),
                "explain":""}
    try:
        rows = run_select(sql)
    except Exception as e:
        return {"question": question,
                "sql": sql,
                "rows":None,
                "error": str(e),
                "explain":""}
    try:
        explain_text, usage = explain(question, sql, rows)
    except Exception as e:

        return {"question": question,
                "sql": sql,
                "rows":rows[0],
                "error": str(e),
                "explain":""}
    return {"question": question,
            "sql": sql,
            "rows":rows,
            "error": None,
            "explain":explain_text}


# ------------------------------------------------------------
# ③ 自检区（不用改）
# ------------------------------------------------------------
def selfcheck():
    print("===== v2-3 自检（会真的调 2 次模型，花几毫钱）=====")
    question = "哪个用户花钱最多"
    print("问题:", question)

    data = run_question(question)
    print("\n返回:", data)

    if not data:
        print("\nFAIL：run_question() 还没返回东西，去 ② 区写 TODO")
        return

    # ⚠️ 契约检查要看"类型"，不能只看"有没有值"。
    #    之前这里写 len(data["rows"])，结果 rows 是 dict 时 len 数的是键的个数，
    #    看着有数、其实形状已经错了，页面渲染才会炸。
    rows = data.get("rows")
    rows_type_ok = isinstance(rows, list) and all(isinstance(r, dict) for r in rows)

    print("\n① SQL      :", data.get("sql"))
    print("② 行数     :", len(rows) if isinstance(rows, list) else f"类型错误({type(rows).__name__})")
    print("③ 数据     :", rows)
    print("④ 错误     :", data.get("error"))
    print("⑤ 人话解释 :", data.get("explain"))
    print("⑥ rows 类型 :", type(rows).__name__, "| 期望 list（元素是 dict），否则页面画不出表格")
    if not rows_type_ok:
        print("   ↑ FAIL：契约要求 list[dict]。如果你写了 rows[0]，页面会报 dict object has no element 0")

    ok = bool(data.get("sql")) and not data.get("error") and rows_type_ok and bool(rows)
    print("\n正常链路判定:", "PASS" if ok else "FAIL")

    # ---- 错误路径：假装模型写了一条危险 SQL ----
    # ⚠️ 坑：这里不能写 import qa 然后 qa.ask_sql = ...
    #    因为文件被当脚本运行时，本模块叫 __main__，import qa 会再加载一次，
    #    变成两个模块对象，patch 的那个 qa.ask_sql 根本不是 run_question 用的那个。
    #    正确做法：直接在"当前模块的全局变量"上换，run_question 查的就是它。
    print("\n--- 模拟：模型写出了 DROP TABLE ---")
    g = globals()
    original = g["ask_sql"]
    g["ask_sql"] = lambda q: {"sql": "DROP TABLE users", "raw": "DROP TABLE users"}
    try:
        bad = run_question("把用户表删了")
    finally:
        g["ask_sql"] = original

    print("返回:", bad)
    if not bad:
        print("FAIL：错误路径没有返回 dict")
        return

    print("SQL 是否就是那条危险语句:", bad.get("sql") == "DROP TABLE users",
          "| 若为 False，说明上面的 patch 没生效，测试是假的")
    guard_ok = (bad.get("error") is not None) and (bad.get("rows") is None)
    print("错误路径判定:", "PASS" if guard_ok else "FAIL（危险 SQL 没被拦下）")

    print("\n最终判定:", "PASS" if (ok and guard_ok) else "FAIL（上面还有 FAIL 项，先修它再往下走）")


if __name__ == "__main__":
    selfcheck()
