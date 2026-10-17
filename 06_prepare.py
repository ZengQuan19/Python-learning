# ============================================================
# 技能 6 / 8：准备训练数据 —— 把表切成模型要的 X 和 y
# 用法：右键 -> Run '06_prepare'
# 数据：loans.csv（贷款审批），目标列是 approved
# ============================================================

import pandas as pd

df = pd.read_csv("loans.csv")

# ------------------------------------------------------------
# 第一部分：热身（不用改，直接运行，对照输出理解）
# ------------------------------------------------------------

print("=== 1. 题目和答案要分家 ===")
y = df["approved"]                       # 答案，单独拎出来
X = df.drop(columns=["approved"])        # 剩下的都是题目
print("y 的形状：", y.shape)
print("X 的形状：", X.shape)
print()

print("=== 2. 删掉 ID 列：流水号对预测毫无用处 ===")
print("删之前有", X.shape[1], "列：", list(X.columns))
X = X.drop(columns=["loan_id"])
print("删之后有", X.shape[1], "列：", list(X.columns))
print()

print("=== 3. 陷阱：用问号表示的『假缺失』 ===")
print("isnull() 检查结果：", X.isnull().any().any(), "  <- 它说没有缺失")
print("但数一数问号，就露馅了：")
print((X == "?").sum())
print()

print("=== 4. 把问号替换成明确的类别 ===")
X = X.replace("?", "unknown")
print("替换后还有问号吗：", (X == "?").any().any())
print()

print("=== 5. One-Hot 编码：全部变成数字 ===")
X = pd.get_dummies(X)
print("编码后 X 的形状：", X.shape)
print("还残留文字列吗：", (X.dtypes == "object").any())
print()
print(X.head())
print()


# ------------------------------------------------------------
# 第二部分：过关任务（在这里作答）
# ------------------------------------------------------------
# 提示：往下写的时候，注意每一步都要把结果「赋值回去」
#      X = X.drop(...)  而不是  X.drop(...)
#      因为你之前踩过这个坑

# TODO 1：把 approved 作为答案 y，其余列作为题目 X
y = df["approved"]
X = df.drop(columns=["approved"])

# TODO 2：从 X 里删掉 loan_id 列
#         要求：删完 X 应该是 5 列
X = X.drop(columns=["loan_id"])

# TODO 3：把 has_house 列里的 "?" 替换成 "unknown"
#         要求：对整张 X 用 replace 就行
#         提示：这题有点绕，想清楚是 X.replace(...) 还是 X["has_house"].replace(...)
#              两种都能做出来，选一种，并想清楚为什么
X = X.replace("?", "unknown")

# TODO 4：对 X 做 One-Hot 编码，结果存回 X
#         要求：X 里不能再有文字列
X = pd.get_dummies(X)


# ------------------------------------------------------------
# 第三部分：自检区（不要改）
# ------------------------------------------------------------
print("===== 自检 =====")
print("y 的形状            ->", y.shape, "| 期望 (15,)")
print("X 的形状            ->", X.shape, "| 期望 (15, 14)")
print("还残留文字列吗      ->", (X.dtypes == "object").any(), "| 期望 False")
print("还有问号吗          ->", (X == "?").any().any(), "| 期望 False")
print("X 里还有 loan_id 吗 ->", "loan_id" in X.columns, "| 期望 False")
