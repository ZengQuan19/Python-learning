# ============================================================
# 抓数据 01：第一次请求 —— 把网上的数据拿到自己手里
# 用法：右键 -> Run '01_first_request'
# 数据源：open-meteo.com（免费、不用注册、不用 API key）
#
# 【载体项目】《天气记录器》
#   每天抓一次真实天气，攒成自己的 CSV，最后用你已经会的 pandas 分析它。
#
# 【本课只学一件事】一次网络请求的完整链路：
#   URL -> status_code -> text / json -> 从里面取出你要的那个数字
#
# 【顺带练的语言功能】
#   JSON 下载下来就是 Python 的 dict（字典）和 list（列表）。
#   所以本课把「怎么一层层取值」练熟，并且学会用 type() 和
#   json.dumps(indent=2) 自己看清结构 —— 这两个自查手段比问人快。
# ============================================================

import json        # 本课只用来把结构打印得好看（indent=2 就是缩进 2 格）
import requests    # 刚修好的库：requests 2.34.2


# ------------------------------------------------------------
# 第 0 步：把要抓的地址写成一个变量
# ------------------------------------------------------------
# URL 里 ? 后面的东西叫「查询参数」，相当于点外卖时的备注：
#   latitude / longitude  北京的经纬度
#   current=...           我要哪几项当前数据（温度、风速、湿度）
#   timezone=...          按哪个时区给时间，不写就是 UTC（跟北京时间差 8 小时）
#
# 为什么写成变量、而不是每个地方复制一遍？
#   以后想换城市只改这一处。这是最基础的「不要重复自己」。
URL_BJ = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=39.9042&longitude=116.4074"
    "&current=temperature_2m,wind_speed_10m,relative_humidity_2m"
    "&timezone=Asia/Shanghai"
)
# 顺便记一个语法细节：上面 4 行字符串外面只有一对括号、没有加号，
# 相邻的字符串字面量会自动拼成一条。这样写长 URL 比写一行好读得多。


# ------------------------------------------------------------
# 第一部分：热身（不用改，直接运行，对照输出理解）
# ------------------------------------------------------------

# --- 1. 发请求 ---
print("=== 1. 发请求 ===")
r = requests.get(URL_BJ, timeout=15)

print("r 的类型：", type(r))
print("   -> 不是字符串！它是 Response 对象，一个「包裹」，里面装着对方回给你的一切。")
print("   -> timeout=15 必须写：不写的话对方不回答，你就永远卡在那一行（真的会卡死）。")
print()

# --- 2. 状态码：这次到底成没成 ---
print("=== 2. r.status_code：服务器给你的第一句话 ===")
print("状态码：", r.status_code)
print("   200 = 成功，东西给你了")
print("   404 = 地址不存在（网址打错了）")
print("   403 = 服务器认出你是脚本，拒绝服务（第 08 课讲怎么处理）")
print("   500 = 对方自己崩了，跟你无关，过一会儿再试")
print()

# --- 3. text：最原始的文本 ---
print("=== 3. r.text：服务器原样回给你的字符串 ===")
print("前 120 个字符：", r.text[:120])
print("类型：", type(r.text), "| 总长度：", len(r.text))
print()

# --- 4. json()：把文本变成 Python 的 dict（本课重点）---
print("=== 4. r.json()：JSON 文本 -> Python 的 dict ===")
d = r.json()
print("d 的类型：", type(d))
print("d 里有哪些键：", list(d.keys()))
print()
print("缩进打印出来看结构：")
print(json.dumps(d, ensure_ascii=False, indent=2))
print("   -> 以后拿到任何不认识的返回，先这样打印一遍。")
print("      看结构永远比猜键名快，这一步能省掉你 80% 的试错。")
print()

# --- 5. 一层层取值：像剥洋葱 ---
print("=== 5. 从嵌套结构里取值 ===")
cur = d["current"]
print("d['current'] 的类型：", type(cur))
print("d['current'] 的键：", list(cur.keys()))
print()

temp = cur["temperature_2m"]
wind = cur["wind_speed_10m"]
hum = cur["relative_humidity_2m"]
print("温度：", temp, "| 类型：", type(temp))
print("   -> 是 float（小数），不是字符串！所以能直接拿去算数。")
print("风速：", wind, "| 湿度：", hum)
print()

# 单位不在 current 里，而是单独放在另一个键里 —— 这是 JSON 的常见套路
print("单位藏在 current_units 里：", d["current_units"])
print()

# --- 6. 拼成人话 ---
print("=== 6. 拼成人话（f-string）===")
print(f"北京 {cur['time']} —— {temp} 度，风速 {wind} km/h，湿度 {hum}%")
print("   -> f-string 里可以直接写下标取值，也能写表达式，比如 {temp + 1}")
print()

# --- 7. 坑①：键名写错 ---
print("=== 7. 坑①：键名写错 = KeyError ===")
try:
    print(d["current"]["sunshine"])
except KeyError as e:
    print("报错原文：KeyError", e)
    print("   -> 意思是「current 里没有 sunshine 这个键」。")
    print("      报错信息里引号包着的那个词，就是让你回去比对结构的地方。")
print()

# --- 8. 坑②：不确定有没有这个键，就用 .get() ---
print("=== 8. 坑②：不确定键存不存在，用 .get() ===")
safe = d["current"].get("sunshine", "没有这个数据")
print(".get('sunshine', 默认值) 的结果：", safe)
print("   -> 键不存在也不崩，给你默认值。")
print("      抓数据经常遇到「这条记录有这项、那条没有」，.get() 是保命写法。")
print()

# --- 9. 边界提醒（第 08 课细讲）---
print("=== 9. 现在就要知道的边界 ===")
print("① 别高频打人家服务器：两次请求之间至少隔几秒")
print("② 别抓需要登录才能看的内容")
print("③ 抓之前看一眼网站的 robots.txt 和使用条款")
print()


# ------------------------------------------------------------
# 第二部分：过关任务（在这里作答）
# ------------------------------------------------------------
# 要求：不要复制粘贴上面的代码，自己敲。
#      做完整个文件跑一次，看最后的自检区。

# TODO 1：抓上海（坐标 latitude=31.2304, longitude=121.4737）
#         - 参照上面的 URL，把经纬度换掉，其他参数照抄
#         - 请求结果存给 r_sh，别忘了 timeout=15
#         - 打印它的状态码
r_sh = None

# TODO 2：从上海的返回里取出当前温度，存给 temp_sh
#         要求：它应该是 float 类型（自己用 type() 打印确认一下）
#         提示：先 r_sh.json()，再一层层剥。
temp_sh = None

# TODO 3：用 .get() 从上海的 current 里取一个「不存在的键」"sunshine"
#         存给 missing_sh，取不到就给字符串 "没有这个数据"
#         要求：这一步不许报错
missing_sh = None

# TODO 4：拼一句人话播报，存给 report_sh
#         形如：上海 2026-10-04T16:15 现在 23.4 度，湿度 60%
#         要求：温度保留一位小数（提示：f-string 里写 {温度:.1f}）
report_sh = None


# ------------------------------------------------------------
# 第三部分：自检区（不要改）
# ------------------------------------------------------------
print("===== 自检 =====")
print("热身：北京状态码 ->", r.status_code, "| 期望 200")
print("热身：北京温度   ->", temp, "| 类型", type(temp).__name__, "| 期望 float，值在 -50 ~ 50 之间（实时数据，不写死）")
print()
print("TODO1 r_sh 状态码 ->", (r_sh.status_code if r_sh is not None else None), "| 期望 200")
print("TODO2 temp_sh     ->", temp_sh, "| 类型", type(temp_sh).__name__,
      "| 期望 float，-50 ~ 50")
print("     自查：(-50 < temp_sh < 50) ->",
      (-50 < temp_sh < 50) if isinstance(temp_sh, (int, float)) else None, "| 期望 True")
print("TODO3 missing_sh  ->", missing_sh, "| 期望 没有这个数据")
print("TODO4 report_sh   ->", report_sh)
print("     自查：里面同时有「上海」和「度」 ->",
      ("上海" in report_sh and "度" in report_sh) if isinstance(report_sh, str) else None,
      "| 期望 True")
print()
print("如果自检全是期望值，说明你已经会「发请求 + 看懂返回 + 取数据」了。")
print("下一课：02——一次抓多个城市，开始用 for 循环。")
