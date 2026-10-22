# ============================================================
# 里程碑 1：Hello, world —— 你的第一个网页
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

from flask import Flask

# Flask(__name__) 的意思是"建一个网站对象，名字叫当前文件"。
# 这个名字后面用来找 templates/、static/ 目录，现在不用深究。
app = Flask(__name__)


# ------------------------------------------------------------
# ① 可运行的热身示例（先跑通，先别改）
# ------------------------------------------------------------
# @app.route("/") 是装饰器：把"路径 -> 函数"登记进路由表。
# 括号里是浏览器地址栏里 127.0.0.1:5000 后面那一段。
# 函数 return 的字符串，就是浏览器里看到的东西。
@app.route("/")
def index():
    return "Hello, 数据分析 Agent! 这是第一个网页。"


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
# ------------------------------------------------------------
# ③ 自检区（不用改）
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


# __name__ == "__main__" 的意思是"这个文件是被直接运行的，不是被 import 的"。
# 只有直接运行才启动服务器；被别的文件 import 时不会自动开服务。
if __name__ == "__main__":
    selfcheck()
    # debug=True：改完代码保存后服务器自动重启，刷新浏览器就能看到新内容；
    #             出错时浏览器里直接显示报错堆栈，对新手非常有用。
    # 注意：debug 模式改代码保存后会自动重启，所以自检可能打印多遍，正常现象。
    app.run(host="127.0.0.1", port=5000, debug=True)
