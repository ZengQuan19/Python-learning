# ============================================================
# 技能 7 / 8：模型训练与验证 —— 第一次让机器自己找规律
# 用法：右键 -> Run '07_model'
# 数据：loans_big.csv（300 条贷款记录）
#
# 【本课只要记住三个动作】
#   model.fit(题目, 答案)      -> 学
#   model.predict(题目)        -> 考
#   打分函数(真答案, 预测)      -> 判
# ============================================================


# ------------------------------------------------------------
# 导入：从哪个工具箱里，拿哪些工具
# ------------------------------------------------------------
# 写法一：import 工具箱 as 昵称  -> 以后用的时候写「昵称.工具名」
import pandas as pd

# 写法二：from 工具箱 import 工具名  -> 以后直接用「工具名」
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report


# ------------------------------------------------------------
# 第一部分：热身（不用改，直接运行，对照下面的注释理解）
# ------------------------------------------------------------

# --- 步骤 1：读数据（技能 3 学过）---
# read_csv 把文件读成一张表；shape 返回 (行数, 列数)
df = pd.read_csv("loans_big.csv")
print("原始数据形状：", df.shape)
print()

# --- 步骤 2：分出题目和答案（技能 6 学过）---
# df["approved"]           -> 取出 answer 那一列，作为答案 y
# df.drop(columns=[...])   -> 把这几列扔掉，剩下的当题目 X
y = df["approved"]
X = df.drop(columns=["approved", "loan_id"])
X = X.replace("?", "unknown")      # 把"假缺失"问号换成明确的 unknown
X = pd.get_dummies(X)              # One-Hot：文字列全部拆成 0/1 数字列

print("题目 X 的形状：", X.shape)
print("答案 y 的形状：", y.shape)
print()


# --- 步骤 3：拆分数据 ---
print("=== 1. 拆分：练习题 vs 考卷 ===")

# 这一行格式特殊：等号左边有 4 个变量，右边只调用了 1 个函数。
# 意思是「这个函数一次吐出 4 样东西，按顺序分别装进左边 4 个盒子」。
# 顺序是固定的、不能调换的：
#     X_train = 练习题（占 80%）
#     X_test  = 考卷  （占 20%）
#     y_train = 练习题的答案
#     y_test  = 考卷的答案
X_train, X_test, y_train, y_test = train_test_split(
    X,                    # 第 1 个参数：全部题目
    y,                    # 第 2 个参数：全部答案
    test_size=0.2,        # 拿 20% 出来当考卷
    random_state=42,      # 随机种子。写死它，每次运行拆分结果都一样
    stratify=y,           # 保证考卷里 yes/no 的比例和原数据一致
)

print("练习题（训练集）：", X_train.shape[0], "条")
print("考卷  （测试集）：", X_test.shape[0], "条")
print()


# --- 步骤 4：训练 ---
print("=== 2. 让模型学习（fit）===")

# 这两行对应"招一个学徒，然后给他看练习册"：
#   第 1 行：new 一个空白的逻辑回归模型，此刻它还什么都不会
#   第 2 行：把练习题和答案一起喂给它，让它自己总结规律
#
#   model.fit(...) 里的「.」读作「的」
#   model.fit  = "model 的 fit 动作"
#   跟你 ATM 里写的 account.deposit(100) 是完全一样的写法：
#   对象.动作(材料)
model = LogisticRegression(max_iter=1000)   # max_iter=1000：最多算 1000 轮，防它半路放弃
model.fit(X_train, y_train)                 # 注意：这里要给「题目 + 答案」
print("学完了")
print()


# --- 步骤 5：预测 ---
print("=== 3. 让模型答考卷（predict）===")

# 关键：这里只给题目，不给答案。
# 因为我们要考的是它「看题猜答案」的能力，不是「抄答案」的能力。
pred = model.predict(X_test)

# pred 是一个 numpy 数组；[:10] 的意思是「取前 10 个」
# y_test 是 pandas 的 Series，要先 .values 变成数组，才能同样用 [:10]
print("模型预测的前 10 个：", pred[:10])
print("真实答案的前 10 个：", y_test.values[:10])
print()


# --- 步骤 6：打分 ---
print("=== 4. 对答案打分 ===")

# 参数顺序要记牢：先「真答案」，后「预测结果」，顺序反了分数会很难看
acc = accuracy_score(y_test, pred)
print("准确率：", acc)
print()

# classification_report 会打印一张详细的成绩单（下一课细讲怎么读）
print(classification_report(y_test, pred))
print()


# ------------------------------------------------------------
# 第二部分：过关任务（在这里作答）
# ------------------------------------------------------------
# 要求：不要复制粘贴上面的代码，自己一个字一个字敲。
#      fit 和 predict 各喂什么、四个变量的顺序，敲一遍胜过看十遍。

# TODO 1：自己完整写一遍流程
#         直接用上面已经准备好的 X 和 y 就行
#         - 用 train_test_split 拆成训练集 / 测试集（4 个变量自己起名）
#         - 建模型，变量名用 model2
#         - 训练
#         - 预测，结果存给 pred2
#
# 在下面这一片空白里写：
#准备训练集和试题
X_train, X_test, y_train, y_test = train_test_split(X, y ,test_size=0.2, random_state=42, stratify=y)
#训练模型
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)
#训练完了,准备答题
pred2 = model.predict(X_test)



# ------------------------------------------------------------------
# TODO 2：算出 model2 在测试集上的准确率，存给 acc2
#         提示：用 accuracy_score，注意两个参数的顺序

acc2 = accuracy_score(y_test, pred2)

# TODO 3：统计 pred2 里 "yes" 和 "no" 各有多少个，存给 pred2_counts
#         提示：pred2 是数组，先 pd.Series(pred2) 变成一列，再用 .value_counts()
pred2_counts = pd.Series(pred2).value_counts()


# ------------------------------------------------------------
# 第三部分：自检区（不要改）
# ------------------------------------------------------------
print("===== 自检 =====")
print("acc2 ->", acc2, "| 期望 0.7 ~ 0.95 之间（瞎猜约 0.5）")
print("预测分布 ->")
print(pred2_counts)
