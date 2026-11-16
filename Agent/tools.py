# ============================================================
# Agent/tools.py —— 工具定义 + 执行器
#
# 【v3 和 v2 的根本区别】
#   v2：模型直接"写 SQL"，我们审核后执行。模型输出的是自由文本，我们只能靠正则白名单兜底。
#   v3：模型不再写 SQL，而是"选工具、给参数"。它只能从下面 TOOLS 里挑一个，
#       参数也必须符合我们给的 JSON Schema。
#
#   安全上的差别很大：
#     - v2 的风险面 = 模型能写出任何 SQL（所以要白名单 + 禁用词 + LIMIT）
#     - v3 的风险面 = 模型只能在既定工具里挑（run_sql 仍然要过闸，但 top_spender 这种
#       语义工具根本不接受 SQL，模型没有发挥空间）
#   这就是"工具调用"在工程上的真正价值：**把开放式的自由生成，收窄成结构化的有限选择**。
#
# 【协议长什么样】
#   请求时带上 tools 清单（名字 + 描述 + 参数的 JSON Schema）。
#   模型不直接回答，而是返回 tool_calls：
#     {"id": "call_xxx", "type": "function",
#      "function": {"name": "run_sql", "arguments": "{\"sql\": \"SELECT ...\"}"}}
#   注意 arguments 是【JSON 字符串】，不是 dict —— 要先 json.loads。
#   我们执行完，把结果以 role="tool" 的消息发回去，模型再给最终答案。
# ============================================================

import json

from db import check_sql, run_select, top_user


# ------------------------------------------------------------
# ① 工具清单：给模型看的"菜单"
# ------------------------------------------------------------
# description 写得好不好，直接决定模型选不选这个工具、参数给得对不对。
# 这不是写给程序员看的注释，是写给模型看的"说明书"。
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": (
                "执行一条只读 MySQL SELECT 查询并返回结果行。"
                "适合需要自己组合条件、聚合、排序的统计问题。"
                "只能用 users / products / orders 三张表。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": (
                            "一条单句 SELECT。表结构："
                            "users(user_id, name, city, signup_date, age)；"
                            "products(product_id, product_name, price, category)；"
                            "orders(order_id, user_id, product_id, quantity, amount, status, order_date)。"
                            "订单状态 status 有 paid/pending/cancelled/refunded，"
                            "问金额时默认只算 paid。"
                        ),
                    }
                },
                "required": ["sql"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "top_spender",
            "description": "直接返回已支付金额最高的用户（姓名、城市、总额、订单数）。不需要参数。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


# ------------------------------------------------------------
# ② 执行器：把模型给的工具名 + 参数，变成真正的数据
# ------------------------------------------------------------
def _tool_run_sql(args):
    sql = args.get("sql", "")
    ok, reason = check_sql(sql)
    if not ok:
        # 注意：工具出错不是"抛异常"，而是"把错误信息当成结果返回给模型"，
        # 让模型看到错误、自己修正 SQL 再试一次（这就是 agent 的自我纠错）。
        return f"错误：SQL 未通过安全校验（{reason}）"
    try:
        rows = run_select(sql)
    except Exception as e:
        return f"错误：查询执行失败（{e}）"
    return json.dumps(rows[:50], ensure_ascii=False, default=str)


def _tool_top_spender(args):
    row = top_user()
    if not row:
        return "没有数据"
    return json.dumps(row, ensure_ascii=False, default=str)


REGISTRY = {
    "run_sql": _tool_run_sql,
    "top_spender": _tool_top_spender,
}


def call_tool(name, arguments):
    """按名字执行工具。arguments 是模型给的 JSON 字符串。

    返回给模型的"工具结果"永远是一段文本（成功或错误说明都行）。
    """
    func = REGISTRY.get(name)
    if func is None:
        return f"错误：不存在的工具 {name}"

    try:
        args = json.loads(arguments) if arguments else {}
    except json.JSONDecodeError:
        return f"错误：工具参数不是合法 JSON：{arguments[:100]}"

    return func(args)


# ------------------------------------------------------------
# ③ 自检区（不用改，不花钱、不调模型）
# ------------------------------------------------------------
def selfcheck():
    print("===== tools.py 自检 =====")
    print("① 工具清单:", [t["function"]["name"] for t in TOOLS])

    print("\n② 正常工具调用 run_sql:")
    print("  ", call_tool("run_sql", '{"sql": "SELECT name FROM users LIMIT 2"}'))

    print("\n③ 危险 SQL 应该返回错误而不是执行:")
    print("  ", call_tool("run_sql", '{"sql": "DROP TABLE users"}'))

    print("\n④ 语义工具 top_spender:")
    print("  ", call_tool("top_spender", "{}"))

    print("\n⑤ 不存在的工具 / 坏参数:")
    print("  ", call_tool("delete_everything", "{}"))
    print("  ", call_tool("run_sql", "{这不是JSON"))


if __name__ == "__main__":
    selfcheck()
