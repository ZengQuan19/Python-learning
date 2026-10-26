# ============================================================
# Agent/llm.py —— 跟大模型说话的这一层
#
# 怎么跑（不用开 Flask）：
#   .venv\Scripts\python.exe Agent\llm.py
#
# 前提：Agent/llm_config.py 里已经填好 API_KEY（那个文件被 .gitignore 排除）
#
# 【这一层做什么】
#   v1 里"问题 -> 查询"是你手写在 index() 里的，只会那一题。
#   v2 把这一步交给模型：把问题 + 表结构发过去，让它写出 SQL。
#   但模型只会"说话"，不会真查库，所以三层分工是：
#       llm.py   问题 -> SQL 文本   （调 API、拼提示词、清洗返回值）
#       db.py    SQL  -> 数据       （连库、执行、拿结果）
#       app.py   把两边串起来 + 显示
#   这也是为什么 v1 要先把 db.py 拆出来：v2 换掉的只是"SQL 从哪来"，执行层不动。
# ============================================================
#
# ============================================================
# 【背景知识】"通过 key 问 AI" 到底发生了什么
# ------------------------------------------------------------
# 1) 你电脑上没有 AI。
#    模型跑在 DeepSeek 的机房服务器上（一个网址：https://api.deepseek.com）。
#    你的程序只是一个"客户端"，把问题用 HTTP 发过去，等它把答案发回来。
#    和浏览器访问网页是同一套东西，只是数据格式是 JSON、不是 HTML。
#
# 2) API key 是什么？
#    那台服务器对全世界开放，但要收钱。它必须知道"这次请求算谁的账"。
#    key（形如 sk-xxxxxxxx）就是你的身份凭证：
#        服务器收到请求 -> 先查这个 key 是否存在、余额够不够 -> 才处理。
#    所以：
#      - key 泄漏 = 别人拿你的钱去跑模型（这就是它不能进 git 的原因）；
#      - key 错了 -> 服务器返回 HTTP 401（我们代码里翻译成人话的那句）；
#      - 余额没了 -> HTTP 402。
#
# 3) 一次调用在网络上到底长什么样？（重点，看懂这段你就懂了）
#
#    请求（你发出去的）：
#        POST https://api.deepseek.com/chat/completions
#        Authorization: Bearer sk-xxxxxxxx      <- key 放这里，不在 URL 里
#        Content-Type: application/json
#
#        {
#          "model": "deepseek-flash",
#          "messages": [
#            {"role": "system", "content": "你是 SQL 生成器，表结构是..."},
#            {"role": "user",   "content": "哪个用户花钱最多"}
#          ],
#          "stream": false,
#          "temperature": 0.2
#        }
#
#    响应（它发回来的）：
#        HTTP/1.1 200 OK
#        Content-Type: application/json
#
#        {
#          "choices": [
#            {"index": 0,
#             "message": {"role": "assistant", "content": "SELECT ..."},
#             "finish_reason": "stop"}
#          ],
#          "usage": {"prompt_tokens": 210, "completion_tokens": 42, "total_tokens": 252}
#        }
#
#    我们的代码只干三件事：
#        a. 拼出上面那个请求（URL、headers、body）
#        b. 发出去，检查状态码
#        c. 从固定位置 choices[0].message.content 把文字挖出来
#
# 4) 为什么必须带 messages 而不是只带一句话？
#    服务器"不记得"你上次问过什么 —— 每次请求都是独立的。
#    你发什么它就看什么，所以上下文必须每次重新发。
#    v3 的"多轮记忆"就是把之前几轮 user/assistant 消息一起塞进 messages。
#
# 5) token 和钱
#    计费单位是 token（约等于 1 个汉字 / 1 个英文词的一部分）。
#    输入（你的 messages）和输出（它的回答）都算钱。usage 里就是这次的账单明细。
#    deepseek-flash 很便宜，但养成看 usage 的习惯。
# ============================================================

import json

import requests

from llm_config import API_KEY, BASE_URL, MODEL

TIMEOUT = 60          # 网络请求最多等 60 秒。不设的话网络卡住，程序会一直等
                      # （在 Web 服务里，这会把处理请求的线程占死）


# ------------------------------------------------------------
# ① 可运行的热身示例（先跑通，先别改）
# ------------------------------------------------------------
def chat(messages, temperature=0.2, debug=False):
    """调一次 DeepSeek，返回 (回答文本, usage 字典)。

    messages 是"对话列表"，格式固定：
        [{"role": "system", "content": "你是...（人设/规则）"},
         {"role": "user",   "content": "用户说的话"}]
    system 放规则，user 放这一句问题。v3 会再加 assistant 的历史回复，形成多轮。

    debug=True 时会把"真实发出去的请求"和"真实收到的响应"打印出来，
    想看懂 API 长什么样，就跑一次带 debug 的（selfcheck 里已经用上了）。
    """
    # --- 1. 拼请求地址：base_url + 接口路径 ---
    # /chat/completions 是"聊天补全"的标准接口，OpenAI 兼容格式，
    # 所以国内大部分模型（DeepSeek、通义、智谱…）都长这样，换个域名就能用。
    url = f"{BASE_URL}/chat/completions"

    # --- 2. 请求头：认证信息 + 数据格式 ---
    # Authorization: Bearer <key> 是 HTTP 认证的标准写法。
    # "Bearer" 的意思是"持有者"：谁拿着这个 key，谁就被当成你。
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",   # 告诉服务器"我发的是 JSON"
    }

    # --- 3. 请求体：告诉它用哪个模型、说什么、要不要流式 ---
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,             # False=一次性返回完整答案；True=打字机效果，v3 再玩
        "temperature": temperature,  # 越低越稳定。写 SQL 用 0~0.3；聊天可以高一点
    }

    if debug:
        print("   [debug] 请求地址 :", url)
        print("   [debug] 请求头   :", {"Authorization": f"Bearer {API_KEY[:5]}******（真实 key 不打印）",
                                        "Content-Type": "application/json"})
        print("   [debug] 请求体   :", json.dumps(payload, ensure_ascii=False)[:500])

    # --- 4. 真正发出去 ---
    # json=payload 会自动做两件事：dict -> JSON 文本、顺便设 Content-Type。
    # 相当于 requests.post(url, data=json.dumps(payload), headers=headers)。
    resp = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)

    # --- 5. 先看状态码，再决定要不要解析 ---
    # 把"网络层的错误码"翻译成"人话"，否则你只会看到一串 401 猜半天。
    if resp.status_code == 401:
        raise RuntimeError("401：API key 不对或没填（检查 Agent/llm_config.py）")
    if resp.status_code == 402:
        raise RuntimeError("402：账户余额不足，去 platform.deepseek.com 充值")
    if resp.status_code == 429:
        raise RuntimeError("429：请求太频繁，等几秒再重试")
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}：{resp.text[:300]}")

    # --- 6. 解析响应 ---
    data = resp.json()                            # JSON 文本 -> dict
    if debug:
        print("   [debug] 响应状态 :", resp.status_code)
        print("   [debug] 响应体   :", json.dumps(data, ensure_ascii=False)[:500])

    # 从固定位置把"回答文字"挖出来：choices 列表的第 0 个、message、content。
    # 为什么要这么绕？因为一个请求可以要多个候选回答（n 参数），默认只返回 1 个。
    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})                 # token 账单，出问题时会没有
    return text, usage


def strip_code_fence(text):
    """模型爱把 SQL 包在 ```sql ... ``` 里，这里把围栏剥掉，只留内容。

    这是跟模型打交道的日常：它输出的是"自然语言文本"，
    你得先清洗成"程序能用的格式"，才能往下走。
    """
    t = text.strip()
    if t.startswith("```"):
        lines = t.splitlines()
        lines = lines[1:]                       # 去掉第一行的 ```sql
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]                  # 去掉最后一行的 ```
        t = "\n".join(lines).strip()
    return t


# ------------------------------------------------------------
# ② 提示词区（TODO 已完成，这里保留讲解）
# ------------------------------------------------------------
# 提示词（system）必须写清三件事，否则模型一定瞎编列名：
#   1. 表结构：有哪些表、哪些列 —— 模型没见过你的数据库
#   2. 口径：业务规则（"花了多少钱"只算 paid、金额列是 amount）—— 模型猜不出来
#   3. 输出格式：只要一条 SELECT，不要解释、不要围栏 —— 方便程序直接用
#
# 注意：写成普通字符串拼接，而不是缩进的 triple-quote。
# 因为缩进的 ''' 会把每行前面的空格也带进提示词，发给模型的文本会长得很怪。

SQL_SYSTEM_PROMPT = (
    "你是一个 MySQL 查询生成器。只输出一条 SELECT 语句，不要解释，不要 markdown 围栏。\n"
    "\n"
    "数据库：practice\n"
    "表结构：\n"
    "  users(user_id, name, city, signup_date, age)\n"
    "  products(product_id, product_name, price, category)\n"
    "  orders(order_id, user_id, product_id, quantity, amount, status, order_date)\n"
    "\n"
    "业务口径：\n"
    "  - orders.status 是支付状态，包括paid / pending / cancelled / refunded\n"
    "  - 金额列是 orders.amount\n"
    "  - 问“花了多少钱”这类问题，没有额外说明时只统计 paid\n"
)



def ask_sql(question):
    """把中文问题翻译成一条 MySQL SELECT。

    返回 {"sql": 清洗后的SQL, "raw": 模型原始输出}
    两个都留着：sql 给程序用，raw 给人排查（模型不听话时能看到它到底说了什么）。
    """
    # 1. 拼消息：system 是规则，user 是这次的问题。顺序很重要 —— 规则先立，问题后问。
    messages = [
        {"role": "system", "content": SQL_SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    # 2. 发请求，拿到文本和 token 账单
    text, usage = chat(messages)

    # 3. 清洗：模型可能带 ```sql 围栏，剥掉
    sql = strip_code_fence(text)

    # 4. 按契约返回 dict（app.py 那层会用到 sql；raw 用于日志/排查）
    return {"sql": sql, "raw": text}


# ------------------------------------------------------------
# ③ 自检区（不用改）
# ------------------------------------------------------------
def selfcheck():
    print("===== v2-1 自检 =====")
    print("模型:", MODEL, "| 地址:", BASE_URL)

    print("\n--- 热身：最简单的调用（带 debug，看真实请求长什么样）---")
    text, usage = chat([{"role": "user", "content": "用一句话解释 SQL 是什么"}], debug=True)
    print("回答:", text.strip())
    print("用量:", usage)

    print("\n--- 中文问题 -> SQL ---")
    result = ask_sql("哪个用户花钱最多")
    print("返回:", result)
    if not result:
        print("FAIL：ask_sql() 还没返回东西")
        return

    sql = result.get("sql", "")
    print("\nSQL:", sql)
    print("\n原始输出:", result.get("raw"))
    if sql.strip().upper().startswith("SELECT"):
        print("\n判定: PASS（拿到一条 SELECT）")
        print("下一步：把这条 SQL 交给 db.py 执行（v2-2）")
    else:
        print("\n判定: FAIL（输出不是 SELECT 开头，检查提示词的'输出格式'那段）")


if __name__ == "__main__":
    selfcheck()
