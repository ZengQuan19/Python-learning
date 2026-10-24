# ============================================================
# 里程碑 1：Hello, world —— 你的第一个网页（已完成）
# 里程碑 2：/top-user —— 让网页返回 JSON（已完成）
# 里程碑 3：templates 页面 + 输入框接到数据库（进行中，见 ⑥ 和 ⑧ 区）
#
# 位置：Agent/ 目录。网页和 Agent 的代码全部放这个文件夹，
#       和原来的 SQL/、Net/、根目录的 pandas 学习脚本分开，
#       以后 v1/v2/v3 都在这里长大，不会互相干扰。
#
# 怎么跑：
#   1. 在 PyCharm 里右键 Agent/app.py -> Run 'app'
#      （Working directory 保持项目根 Python 就行，现在还没用到相对路径）
#   2. 浏览器打开 http://127.0.0.1:5000
#   3. 想停：PyCharm 里点红色方块，或在终端里按 Ctrl+C
#   注意：如果你之前用旧路径跑过 app.py，PyCharm 里那条 Run 配置会失效，
#        右键新路径重新 Run 一次即可。
#
# 【先搞懂它为什么能跑】
#   Flask 启动后，你的电脑上多了一个"服务员"，蹲在 5000 号端口等请求。
#   浏览器访问 http://127.0.0.1:5000/ping 时，发生了四件事：
#     ① 浏览器发出一个 HTTP 请求：GET /ping
#     ② Flask 收到请求，拿路径 "/ping" 去路由表里找对应的函数
#     ③ 找到 ping()，执行它 -> 返回字符串 "pong"
#     ④ Flask 把这个字符串包成 HTTP 响应，发回浏览器，浏览器显示出来
#   Web 开发的全部核心就是这一条链路：请求进来 -> 路由找函数 -> 函数返回内容。
# ============================================================

from flask import Flask, jsonify, render_template, request

# Flask(__name__) 的意思是"建一个网站对象，名字叫当前文件"。
# 这个名字后面用来找 templates/、static/ 目录，现在不用深究。
app = Flask(__name__)

# 让 JSON 里的中文原样输出，而不是 \u6df1\u5733 这种转义。
# 转义不算错（浏览器/程序都能解回来），但调试时肉眼读中文更直观。
# 顺便记住：这是 Flask 3 的应用级配置，不是 Python 语法。
app.json.ensure_ascii = False


# ------------------------------------------------------------
# ① 可运行的热身示例（里程碑 3 会让你改 index 的 return）
# ------------------------------------------------------------
# @app.route("/") 是装饰器：把"路径 -> 函数"登记进路由表。
# 括号里是浏览器地址栏里 127.0.0.1:5000 后面那一段。
# 函数 return 的字符串，就是浏览器里看到的东西。
@app.route("/")
def index():
    from db import top_user
    q = request.args.get("q","").strip()
    result = top_user() if q else None
    return render_template("index.html", title = "数据分析 Agent v1",q = q, result = result)


@app.route("/ping")
def ping():
    # 访问 /ping 会看到 pong。用来看服务是不是还活着。
    return "pong"


# ------------------------------------------------------------
# ② TODO 区（留 None，你自己填）
# ------------------------------------------------------------
# 任务：加第三个页面 /about，显示你自己的名字。
#
#   第 1 步：在 def about() 上面加一行装饰器   @app.route("/about")
#   第 2 步：把 return 的内容换成你的自我介绍，比如
#            f"<h1>我是 {MY_NAME}</h1><p>正在从零做数据分析 Agent</p>"
#            （字符串里可以写 HTML 标签，浏览器会把它当网页渲染）
#   第 3 步：保存 -> 刷新 http://127.0.0.1:5000/about 看效果
#
# 提示：
#   - 函数名不能和 index / ping 重名
#   - 返回 HTML 标签时，字符串前面加 f 才能把 {MY_NAME} 替换成变量的值
#   - 没加装饰器时访问 /about 会看到 404 Not Found，这是"没登记到路由表"的表现
MY_NAME = "拙千"              # <- 填你的名字，比如 "Zq118"

@app.route("/about")
def about():
    # TODO: 给这个函数加装饰器，并改掉下面的 return
    return f"""<h1>我是{MY_NAME}</h1>
    <p>正在从零学习Python，以后计划做智能体应用与agent开发行业</p>
    <ul><li>已学:SQL</li><li>在学:Flask</li><li>下一步:数据分析agent</li></ul>
    <a href='https://github.com/ZengQuan19/Python-learning'>点击跳转至我的Python学习仓库(github)</a>"""


# ============================================================
# ④ 里程碑 2：让网页返回 JSON —— /top-user
# ============================================================
# 【为什么这一步要 JSON，不要 HTML 页面】
#   网页是给"人"看的，JSON 是给"程序"看的。
#   v2 的 LLM、v3 的工具调用，要的都是结构化数据，不是一段 HTML。
#   JSON 就是一种文本格式：{"键": 值, ...}，浏览器、Python、JavaScript 都认。
#   Python 的 dict 和 JSON 长得几乎一样，所以 dict 能直接变成 JSON。


# ---------- 热身：这个路由已经写好了，先跑起来看效果 ----------
@app.route("/demo-json")
def demo_json():
    # 对比着看两个路由的返回：
    #   /about      return 字符串    -> Content-Type: text/html，浏览器渲染成页面
    #   /demo-json  return jsonify() -> Content-Type: application/json，浏览器只显示原始文本
    # 打开浏览器开发者工具（F12）-> Network，点一下请求，能看到响应头里的 Content-Type。
    return jsonify({"hello": "world", "from": "Flask", "list": [1, 2, 3]})


# ---------- TODO：把 db.py 的 top_user() 接到网页上 ----------
# 目标：浏览器访问 http://127.0.0.1:5000/top-user 看到这样一行：
#   {"city": "深圳", "name": "孙悦", "orders": 4, "total": 4112.0, "user_id": 11}
#   （键的顺序无所谓，JSON 本身不保证顺序）
#
# 三件事：
#   1. 文件顶部补一行 import：from db import top_user
#      —— db.py 就在同一个 Agent/ 目录，直接 import，不用写路径
#   2. 给下面的函数加装饰器 @app.route("/top-user")
#   3. 函数体写两行：
#        row = top_user()     # 拿到一个 dict（查不到是 None）
#        return jsonify(row)  # dict -> JSON 响应
#
# 提示（先自己想，卡住再看）：
#   - 你的 db.py 里 total 必须已经是 float，否则这里会报
#     "Object of type Decimal is not JSON serializable" —— 这就是 TODO 要求 4 的意义
#   - 想更严谨：top_user() 返回 None 时写成
#        return jsonify({"error": "没有数据"}), 404
#     （return 元组 = (响应体, 状态码)，后面 v1 完整版会用到）

@app.route("/top-user")
def top_user_api():
    # TODO: 先加装饰器，再把这两行补上
    from db import top_user
    return top_user()


# ------------------------------------------------------------
# ③ 自检区（里程碑 1，不用改）
# ------------------------------------------------------------
# 期望的路由表：跑起来后必须包含这三个路径
EXPECTED = {"/", "/ping", "/about"}


def selfcheck():
    print("===== 自检 =====")
    # app.url_map 就是 Flask 的路由表；iter_rules() 遍历里面每条规则
    actual = sorted(str(r) for r in app.url_map.iter_rules() if "static" not in str(r))
    print("① 实际注册的路由：", actual)
    print("   期望包含      ：/  /ping  /about")

    missing = sorted(EXPECTED - set(actual))
    if missing:
        print("② 还缺：", missing, " <- 去 ② 区把装饰器补上")
    else:
        print("② 路由齐全 [OK]")

    print("③ MY_NAME =", repr(MY_NAME), "| 期望：你自己的名字")
    print("   浏览器访问 http://127.0.0.1:5000/about 应该看到你的名字")
    print()


# ------------------------------------------------------------
# ⑤ 自检区（里程碑 2，不用改）
# ------------------------------------------------------------
def check_json_api():
    print("===== 里程碑 2 自检 =====")
    routes = sorted(str(r) for r in app.url_map.iter_rules() if "static" not in str(r))

    # 先看热身路由通不通（它不依赖数据库）
    with app.test_client() as client:
        demo = client.get("/demo-json")
    print("① /demo-json ->", demo.status_code, "|", demo.headers.get("Content-Type"))
    print("   期望 200 | application/json")

    if "/top-user" not in routes:
        print("② /top-user 还没注册 <- 去 ④ 区给 top_user_api 加装饰器")
        print("   当前路由表:", routes)
        print()
        return

    # test_client：不启动服务器、不开浏览器，就能在代码里模拟一次真实 HTTP 请求。
    # 以后写自动化测试（pytest）靠的就是它，现在先感受一下。
    with app.test_client() as client:
        resp = client.get("/top-user")
        print("③ /top-user 状态码      :", resp.status_code, "| 期望 200")
        print("④ /top-user Content-Type:", resp.headers.get("Content-Type"), "| 期望含 application/json")
        print("⑤ /top-user 响应正文    :", resp.get_data(as_text=True))
    print('   期望形如: {"city":"深圳","name":"孙悦","orders":4,"total":4112.0,"user_id":11}')
    print()


# ============================================================
# ⑥ 里程碑 3：HTML 页面 —— 输入框 + 提交按钮
# ============================================================
# 【这一步在解决什么】
#   到现在为止，/about 的 HTML 是塞在 Python 字符串里的：
#       return f"<h1>我是{MY_NAME}</h1>..."
#   页面一复杂这种写法就崩：引号难写、不能复用、改样式要动 Python。
#   所以 Flask 约定一个目录：templates/（模板目录），HTML 单独放里面。
#   Flask 只认 app.py 同级的 templates/，所以目录名不能改。
#
#   把它理解成"填空题"：
#     templates/index.html         —— 带空格的卷子，{{ title }} 就是空格
#     render_template("index.html", title="...") —— 交答案，把空格填上
#   返回值仍然是字符串（完整 HTML），只是不用你自己拼了。
#
# ------------------- TODO（你要做的） -------------------
#   去本文件 ① 区，改掉 index() 的 return（大约第 40 行）：
#       return render_template("index.html", title="数据分析 Agent v1")
#   然后保存、刷新 http://127.0.0.1:5000/ ，应该看到输入框 + 提问按钮。
#
#   （render_template 我已经在顶部 import 好了，不用你加）
#
# 【顺手观察】在输入框里打"哪个用户花钱最多"，点"提问"，看地址栏：
#   http://127.0.0.1:5000/?q=哪个用户花钱最多
#   这就是 GET 请求：表单数据拼在 URL 的 ? 后面，name="q" 变成了参数名 q。
#   页面暂时没反应是正常的 —— 下一步（3b）才把 q 读出来。


# ------------------------------------------------------------
# ⑦ 自检区（里程碑 3，不用改）
# ------------------------------------------------------------
def check_page():
    print("===== 里程碑 3 自检 =====")
    with app.test_client() as client:
        resp = client.get("/")
        html = resp.get_data(as_text=True)

    print("① GET / 状态码   :", resp.status_code, "| 期望 200")
    print("② Content-Type   :", resp.headers.get("Content-Type"), "| 期望含 text/html")
    print("③ 有 <form 吗    :", "<form" in html, "| 期望 True")
    print('④ 有 name="q" 吗 :', 'name="q"' in html, "| 期望 True")
    print("⑤ 标题填上了吗    :", "数据分析 Agent v1" in html, "| 期望 True")
    print("   页面开头预览:", html.strip().splitlines()[:3])
    if "<form" not in html:
        print("   提示：/ 还在 return 字符串，去 ① 区把 index() 改成 render_template")
    print()


# ============================================================
# ⑧ 里程碑 3b：把输入框接到数据库（v1 的主体）
# ============================================================
# 【目标】浏览器提问 -> 服务器读到问题 -> 查库 -> 把结果填回页面。
#   这就是 v1 的完整链路。v2 只替换中间一步（"问题 -> SQL"），两头都不动。
#
# ---------- 热身：读 URL 参数（已写好，先跑起来看效果）----------
# 打开 http://127.0.0.1:5000/echo?q=你好&n=3
# 会看到：q='你好' | n='3' | type(n)=str | 全部参数={...}
# 三个要点：
#   ① request.args 是"URL 里 ? 后面的参数"的字典，.get("q") 取名字叫 q 的值
#   ② .get("q", "") 第二个参数是默认值：没传 q 时返回 ""，不会 KeyError
#   ③ URL 参数永远是字符串：传 3 拿到的也是 "3"，要算数得 int(...)
@app.route("/echo")
def echo():
    q = request.args.get("q", "")
    n = request.args.get("n", "0")
    return f"q={q!r} | n={n!r} | type(n)={type(n).__name__} | 全部参数={dict(request.args)}"


# ---------- TODO A：改 ① 区的 index()（三行，顺序别乱）----------
#   1. q = request.args.get("q", "").strip()
#      .strip() 去掉首尾空格：用户只打了空格，等于没提问
#   2. result = top_user() if q else None
#      没问题就不查库（省一次数据库往返）
#   3. return render_template("index.html", title="数据分析 Agent v1", q=q, result=result)
#      把两个变量一起填进模板
#
#   别忘了 top_user 的 import：它现在写在 /top-user 函数里面（局部 import），
#   index() 里用不到。建议把 from db import top_user 挪到文件顶部，更规范。
#
# ---------- TODO B：改 templates/index.html ----------
#   在 <div id="result"> 里面写 Jinja 条件块：
#     - 只有 q 非空时才显示
#     - 显示一行："你问的是" + q 的值
#     - result 有值时显示：姓名、城市、已支付总额、订单数
#     - result 是 None 时显示"没查到数据"
#   提示：result 是 dict，模板里 result.name 和 result["name"] 两种写法都行
#   提示：Jinja 注释写 {# ... #}，别再往 HTML 注释里写 Jinja 标签（上次那个坑）


# ------------------------------------------------------------
# ⑨ 自检区（里程碑 3b，不用改）
# ------------------------------------------------------------
def check_v1_flow():
    print("===== 里程碑 3b 自检 =====")
    # 问题前面加"测试问题："，避免和页面上那句示例文字撞车（撞了会误判成"已回显"）
    question = "测试问题：哪个用户花钱最多"
    with app.test_client() as client:
        plain = client.get("/")
        resp = client.get("/?q=" + question)
    html = resp.get_data(as_text=True)

    print("① 首页（不带 q）  :", plain.status_code, "| 期望 200")
    print("② 带问题访问       :", resp.status_code, "| 期望 200")
    print("③ 页面回显了问题吗 :", question in html, "| 期望 True")
    print("④ 显示了用户名吗   :", "孙悦" in html, "| 期望 True")
    print("⑤ 显示了金额吗     :", "4112" in html, "| 期望 True")
    if question not in html:
        print("   ③ 失败：index() 没把 q 传给模板，或模板里没有显示 q 的 Jinja 块")
    if "孙悦" not in html:
        print("   ④ 失败：index() 没把 result 传给模板，或模板里没显示 result")
    print()


# __name__ == "__main__" 的意思是"这个文件是被直接运行的，不是被 import 的"。
# 只有直接运行才启动服务器；被别的文件 import 时不会自动开服务。
if __name__ == "__main__":
    selfcheck()
    check_json_api()
    check_page()
    check_v1_flow()
    # debug=True：改完代码保存后服务器自动重启，刷新浏览器就能看到新内容；
    #             出错时浏览器里直接显示报错堆栈，对新手非常有用。
    # 注意：debug 模式改代码保存后会自动重启，所以自检可能打印多遍，正常现象。
    app.run(host="127.0.0.1", port=5000, debug=True)
