# ============================================================
# 技能 9：预测全新的数据 —— 最后一公里
# 用法：右键 -> Run '09_predict'
# 数据：loans_big.csv（带答案，用来训练）+ loans_new.csv（不带答案，用来预测）
#
# 【本课的核心】
#   新数据必须走「一模一样的预处理流水线」。
#   少一步、顺序错一步、或者偷偷重新 fit，都会让预测报废。
# ============================================================

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score


# ------------------------------------------------------------
# 第 0 步：先用老数据把模型训出来（前几课内容，复习）
# ------------------------------------------------------------
print("=== 0. 训练模型 ===")

df = pd.read_csv("loans_big.csv")
y = df["approved"]
X = df.drop(columns=["approved", "loan_id"])
X = X.replace("?", "unknown")
X = pd.get_dummies(X)

print("训练时用的题目列（共", X.shape[1], "列）：")
print(list(X.columns))
print()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)   # 训练集：fit_transform
X_test_scaled = scaler.transform(X_test)         # 测试集：transform

model = LogisticRegression(max_iter=1000)
model.fit(X_train_scaled, y_train)

acc = accuracy_score(y_test, model.predict(X_test_scaled))
print("模型训练完成，测试集准确率：", round(acc, 4))
print()


# ------------------------------------------------------------
# 第一部分：热身 —— 把新数据喂给模型
# ------------------------------------------------------------

print("=== 1. 新数据来了 ===")
new_df = pd.read_csv("loans_new.csv")
print("新数据形状：", new_df.shape)
print("注意它没有 approved 列——因为答案正是我们要预测的东西")
print()

# --- 流水线第 1 站：同样的删列 ---
print("=== 2. 预处理① 删掉 loan_id ===")
new_X = new_df.drop(columns=["loan_id"])
print("删完：", new_X.shape)
print()

# --- 流水线第 2 站：同样的替换 ---
new_X = new_X.replace("?", "unknown")

# --- 流水线第 3 站：同样的 One-Hot ---
print("=== 3. 预处理② One-Hot 编码 ===")
new_X = pd.get_dummies(new_X)
print("编码后：", new_X.shape)
print()

# --- 流水线第 4 站：列对齐（最容易翻车的一站）---
print("=== 4. 预处理③ 列对齐 ===")
print("训练集有", X.shape[1], "列，新数据编码后只有", new_X.shape[1], "列")
print("   -> 数目不一样，直接拿去 predict 会报错")

new_X = new_X.reindex(columns=X.columns, fill_value=0)
print("对齐后：", new_X.shape)

# reindex 做了两件事：
#   1. 新数据缺的列 -> 补上，填 0（表示「这一类对它不成立」）
#   2. 新数据多出来的列（训练时没见过的类别）-> 丢掉
# 这正是技能 5 讲过的那个坑，现在真正用上了。
print()

# --- 流水线第 5 站：用训练时的 scaler，而不是重新 fit ---
print("=== 5. 预处理④ 用训练时的 scaler 转换 ===")
print("这里是 transform，不是 fit_transform！")
print("   -> 标准必须沿用训练时定下的，不能拿新数据重新统计")

new_X_scaled = scaler.transform(new_X)
print()

# --- 预测 ---
print("=== 6. 预测 ===")
new_pred = model.predict(new_X_scaled)
print("预测结果：", new_pred)
print("预测条数：", len(new_pred))
print()
print("结果分布：")
print(pd.Series(new_pred).value_counts())
print()


# ------------------------------------------------------------
# 第二部分：过关任务（在这里作答）
# ------------------------------------------------------------
# 要求：完整走一遍流水线，一步都不能少。

# TODO 1：读入 loans_new.csv，做完整预处理并预测，结果存给 pred_final
#         流水线：读文件 -> drop loan_id -> replace "?" ->
#                 get_dummies -> reindex(columns=X.columns, fill_value=0) ->
#                 scaler.transform -> model.predict
#
# 在下面这一片空白里写：
FX = pd.read_csv("loans_new.csv")
FX = FX.drop(columns=["loan_id"])
FX = FX.replace("?", "unknown")
FX = pd.get_dummies(FX)
FX = FX.reindex(columns=X.columns, fill_value=0)
FX_scaled = scaler.transform(FX)
pred_final = model.predict(FX_scaled)


# ------------------------------------------------------------------
# TODO 2：pred_final 有多少条？存给 n_pred
n_pred = len(pred_final)

# TODO 3：统计 pred_final 里 yes / no 各多少个，存给 final_counts
final_counts = pd.Series(pred_final).value_counts()


# ------------------------------------------------------------
# 第三部分：自检区（不要改）
# ------------------------------------------------------------
print("===== 自检 =====")
print("预测条数 ->", n_pred, "| 期望 20")
print("跟新数据的行数一致吗 ->", n_pred == len(new_df), "| 期望 True")
print("分布 ->")
print(final_counts)
