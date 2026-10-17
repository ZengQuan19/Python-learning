# ============================================================
# 技能 8：把模型调好 —— 标准化 + 换个更强的模型
# 用法：右键 -> Run '08_improve'
# 数据：loans_big.csv
#
# 【本课两件事】
#   1. 用标准化解决上一课的 ConvergenceWarning
#   2. 换一个模型，和逻辑回归比一比
# ============================================================

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report


# ------------------------------------------------------------
# 步骤 0：准备数据（技能 6 复习，直接沿用）
# ------------------------------------------------------------
df = pd.read_csv("loans_big.csv")
y = df["approved"]
X = df.drop(columns=["approved", "loan_id"])
X = X.replace("?", "unknown")
X = pd.get_dummies(X)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print("数据准备好了：题目", X.shape, "，答案", y.shape)
print()


# ------------------------------------------------------------
# 第一部分：热身（不用改，直接运行）
# ------------------------------------------------------------

# --- 1. 标准化 ---
print("=== 1. 标准化：把各列的『音量』调到同一水平 ===")

# StandardScaler 会把每一列都变成「平均值 0、标准差 1」的尺度。
# 这样 income（几万）和 age（几十）就不会一个压死另一个了。
scaler = StandardScaler()

# ⚠️ 最关键的坑：训练集用 fit_transform，测试集用 transform
#    fit_transform = 先学习这列的均值和标准差，再转换   <- 只对训练集做
#    transform     = 用「已经学好的」均值和标准差来转换  <- 测试集只能做这个
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 看一眼 income 这一列转换前后的变化
income_idx = list(X.columns).index("income")
print("标准化前 income 前 3 个：", X_train["income"].values[:3])
print("标准化后 income 前 3 个：", X_train_scaled[:3, income_idx].round(3))
print("   -> 数字变小了、有正有负，但『谁大谁小』的顺序完全没变")
print()

# --- 2. 用标准化后的数据再训一次逻辑回归 ---
print("=== 2. 标准化后的逻辑回归 ===")
model_lr = LogisticRegression(max_iter=1000)
model_lr.fit(X_train_scaled, y_train)       # 注意：喂的是 scaled 版本
pred_lr = model_lr.predict(X_test_scaled)
acc_lr = accuracy_score(y_test, pred_lr)
print("准确率：", acc_lr)
print("   -> 如果这次没再出现 ConvergenceWarning，说明标准化起效了")
print()
print(classification_report(y_test, pred_lr))
print()

# --- 3. 换一个模型：随机森林 ---
print("=== 3. 随机森林：不用标准化也能跑 ===")

# 随机森林 = 造 100 棵决策树，每棵看一部分数据和特征，最后投票。
# n_estimators=100 就是「造 100 棵树」。random_state=42 同样是为了结果可复现。
model_rf = RandomForestClassifier(n_estimators=100, random_state=42)

# 注意：这里喂的是「没标准化」的 X_train / X_test
# 因为树模型只比较大小（大于 60 吗？），不做加减乘除，所以不怕尺度差异
model_rf.fit(X_train, y_train)
pred_rf = model_rf.predict(X_test)
acc_rf = accuracy_score(y_test, pred_rf)
print("准确率：", acc_rf)
print()
print(classification_report(y_test, pred_rf))
print()

print("=== 对比 ===")
print("逻辑回归（标准化后）：", round(acc_lr, 4))
print("随机森林：           ", round(acc_rf, 4))
print()


# ------------------------------------------------------------
# 第二部分：过关任务（在这里作答）
# ------------------------------------------------------------
# 要求：仍然不要复制粘贴，自己敲。

# TODO 1：把「标准化 + 逻辑回归」的流程自己写一遍
#         变量名：scaler2 / model_lr2 / pred_lr2 / acc_lr2
#         记得：训练集 fit_transform，测试集 transform
#
# 在下面这一片空白里写：
scaler2 = StandardScaler()
X_train_scaled2 = scaler2.fit_transform(X_train)
X_test_scaled2 = scaler2.transform(X_test)
#标准化准备完成
model_lr2 = LogisticRegression(max_iter=1000)
model_lr2.fit(X_train_scaled2, y_train)
#训练完成
pred_lr2 = model_lr2.predict(X_test_scaled2)
acc_lr2 = accuracy_score(y_test, pred_lr2)
#预测完成

# ------------------------------------------------------------------
# TODO 2：训练一个随机森林
#         变量名：model_rf2 / pred_rf2 / acc_rf2
#         记得：随机森林不做标准化，直接喂 X_train / X_test
model_rf2 = RandomForestClassifier(n_estimators=100, random_state=42)
#随机树制造
model_rf2.fit(X_train, y_train)
#训练
pred_rf2 = model_rf2.predict(X_test)
#预测
acc_rf2 = accuracy_score(y_test, pred_rf2)
#准确率
# TODO 3：把准确率更高的那个模型的预测结果，存给 best_pred
#         提示：一个 if 判断就够了
best_pred = pred_rf2 if acc_rf2 > acc_lr2 else pred_lr2



# ------------------------------------------------------------
# 第三部分：自检区（不要改）
# ------------------------------------------------------------
print("===== 自检 =====")
print("标准化+逻辑回归 acc_lr2 ->", acc_lr2)
print("随机森林 acc_rf2        ->", acc_rf2)
print("best_pred 的长度        ->", len(best_pred), "| 期望 60")
