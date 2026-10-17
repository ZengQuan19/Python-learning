# ============================================================
# 技能 10：类别不平衡 —— 准确率高，不代表模型好
# 用法：右键 -> Run '10_imbalance'
# 数据：loans_big.csv（300 条，65% yes / 35% no）
#
# 【本课的核心】
#   当两类的数量差得多时，accuracy 会被多数类绑架。
#   一个「永远说 yes」的模型准确率就有 65%，但它对 no 一无所获。
#   所以本课三件事：
#     ① 先看分布，再谈分数
#     ② 别只用 accuracy 打分，要看少数类的 recall
#     ③ 用 class_weight="balanced" 让模型对少数类的错误更敏感
#
# 【本课新词】
#   多数类(majority) / 少数类(minority)：样本多的那类 / 少的那类
#   recall（召回率）：真正该抓的里面，抓到了几个  = 抓对 / 该抓的全部
#   precision（精确率）：抓出来的人里面，有几个是真该抓的
#   混淆矩阵：把「对/错」拆成 4 格的表格，比一个总分信息量大得多
# ============================================================

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


# ------------------------------------------------------------
# 第 0 步：准备数据（技能 6 / 7 的流水线，原样沿用）
# ------------------------------------------------------------
df = pd.read_csv("loans_big.csv")
y = df["approved"]
X = df.drop(columns=["approved", "loan_id"])
X = X.replace("?", "unknown")
X = pd.get_dummies(X)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)


# ------------------------------------------------------------
# 第一部分：热身（不用改，直接运行，对照注释理解）
# ------------------------------------------------------------

# --- 1. 动手之前先看分布 ---
print("=== 1. 先看答案的分布 ===")
print(df["approved"].value_counts())
print()
# normalize=True 不算个数，算占比。这一步是判断「有没有不平衡」的起点。
print(df["approved"].value_counts(normalize=True).round(3))
print("   -> yes 占 65%，no 只有 35%。多数类是 yes。")
print()

# --- 2. 无脑基线：一个什么都不学的模型 ---
print("=== 2. 无脑基线：永远猜多数类 ===")
# DummyClassifier 是 sklearn 自带的"陪练"：它完全不看题目，
# strategy="most_frequent" 的意思是「训练集里哪类多，我就永远答哪类」。
# 它的作用不是拿来用的，而是拿来当"地板线"的。
dummy = DummyClassifier(strategy="most_frequent")
dummy.fit(X_train, y_train)
pred_dummy = dummy.predict(X_test)
dummy_acc = accuracy_score(y_test, pred_dummy)
print("无脑基线准确率：", round(dummy_acc, 4))
print(classification_report(y_test, pred_dummy, zero_division=0))
print("   -> 看 no 那一行：recall = 0.00。")
print("      也就是说 65% 的准确率是白来的，no 一个都没抓对。")
print("      这就是「准确率的陷阱」：只有跟这条地板线比，你才知道模型有没有真本事。")
print()

# --- 3. 普通逻辑回归 ---
print("=== 3. 普通逻辑回归（不加权）===")
# 标准化：训练集 fit_transform，测试集 transform（技能 8 的铁律）
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model_lr = LogisticRegression(max_iter=1000)
model_lr.fit(X_train_scaled, y_train)
pred_lr = model_lr.predict(X_test_scaled)
acc_lr = accuracy_score(y_test, pred_lr)
print("准确率：", round(acc_lr, 4))
print(classification_report(y_test, pred_lr))
print()

# --- 4. 同一份数据，换 class_weight ---
print("=== 4. class_weight='balanced'：让少数类「更值钱」===")
# 默认情况下，模型眼里每个样本一样重：错一个 yes 和错一个 no 代价相同。
# 但 no 只有 35%，就算全部答成 yes，损失也不大 —— 模型没有动力去学 no。
#
# class_weight="balanced" 做的事：按类别数量自动反比加权。
# 样本少的类，每个样本算"更重"，所以错一个 no 的惩罚 >> 错一个 yes。
# 结果：模型开始认真对待 no，代价是有时会把 yes 误判成 no。
#
# ⚠️ 注意它改的是"模型怎么学"，没有改任何一行数据。
model_bal = LogisticRegression(max_iter=1000, class_weight="balanced")
model_bal.fit(X_train_scaled, y_train)
pred_bal = model_bal.predict(X_test_scaled)
acc_bal = accuracy_score(y_test, pred_bal)
print("准确率：", round(acc_bal, 4))
print(classification_report(y_test, pred_bal))
print()

# --- 5. 把错误拆开看：混淆矩阵 ---
print("=== 5. 混淆矩阵：4 格比 1 个分数有用 ===")
# labels 决定了行和列的顺序。这里显式写出来，避免"字母序"这种隐形约定。
# 行 = 真实答案，列 = 模型预测。
cm = confusion_matrix(y_test, pred_bal, labels=["no", "yes"])
print("          预测no  预测yes")
print("真实no  ", cm[0])
print("真实yes ", cm[1])
print()
# 读法（我们关心的是少数类 no）：
#   cm[0][0] = 真实 no，判成 no  -> 抓对了
#   cm[0][1] = 真实 no，判成 yes -> 漏掉了   ← 这一类错误最要命
#   cm[1][0] = 真实 yes，判成 no -> 误报
#   cm[1][1] = 真实 yes，判成 yes-> 抓对了
#   recall(no)    = cm[0][0] / (cm[0][0] + cm[0][1])   漏掉越少越高
#   precision(no) = cm[0][0] / (cm[0][0] + cm[1][0])   误报越少越高
print()

# --- 6. 三种做法排一起对比 ---
print("=== 6. 对比 ===")
# 下面 no 的那三个 recall，是从上面三份 classification_report 里抄下来的，
# 抄到一张表里，方便横着比。
print(f"{'做法':<22}{'accuracy':>10}{'no的recall':>12}")
print(f"{'无脑基线':<22}{dummy_acc:>10.4f}{0.0:>12.2f}")
print(f"{'逻辑回归':<22}{acc_lr:>10.4f}{0.52:>12.2f}")
print(f"{'逻辑回归+balanced':<22}{acc_bal:>10.4f}{0.81:>12.2f}")
print()
print("   -> balanced 之后：no 的 recall 从 0.52 涨到 0.81。")
print("      这就是「处理不平衡」的实际效果：牺牲一点点别的，换回少数类。")
print()


# ------------------------------------------------------------
# 第二部分：过关任务（在这里作答，先别删下面的 None）
# ------------------------------------------------------------
# 要求：不要复制粘贴上面的代码，自己敲。做完跑一次，把控制台输出留着。

# TODO 1：自己训练一个 class_weight="balanced" 的逻辑回归
#         - 用上面已经标准化好的 X_train_scaled / X_test_scaled
#         - 模型变量名 model_bal2，预测结果 pred_bal2，准确率 acc_bal2
#         - 再用 classification_report 打印一次
#         把模型的预测结果存给 pred_bal2 下面这个变量

model_bal2 = None        # 换成你建的模型
pred_bal2 = None         # 换成你的预测结果
acc_bal2 = None          # 换成你的准确率

# ------------------------------------------------------------------
# TODO 2：从混淆矩阵里把 4 个数分别取出来
#         - 用 confusion_matrix(y_test, pred_bal2, labels=["no", "yes"])
#         - 把 cm[0][0] / cm[0][1] / cm[1][0] / cm[1][1] 分别存给
#           no_as_no / no_as_yes / yes_as_no / yes_as_yes
#         提示：矩阵是二维的，用两个下标取。先 print 出来看看形状对不对。

no_as_no = None
no_as_yes = None
yes_as_no = None
yes_as_yes = None

# ------------------------------------------------------------------
# TODO 3：不看 classification_report，自己从这 4 个数算出 no 的 recall 和 precision
#         - recall_no_2     = ?
#         - precision_no_2  = ?
#         算完，跟 TODO 1 打印出来的 report 对一下：一样吗？
#         这是本课的第二个重点：能自己算出来，才算真懂这两个指标。

recall_no_2 = None
precision_no_2 = None

# ------------------------------------------------------------------
# TODO 4（不写代码，写在注释里就行）：思考题
#         银行的场景是"批准贷款"：
#         把该批的人拒了（误拒）和把不该批的人批了（坏账），哪个代价更大？
#         如果代价不对等，你觉得该动哪个旋钮？
#         提示：class_weight 是本课给你的第一个旋钮。

# 你的答案：


# ------------------------------------------------------------
# 第三部分：自检区（不要改）
# ------------------------------------------------------------
print("===== 自检 =====")
print("无脑基线 dummy_acc   ->", dummy_acc, "| 期望 ≈ 0.65（就是多数类占比）")
print("普通逻辑回归 acc_lr  ->", acc_lr, "| 期望 ≈ 0.72")
print("balanced acc_bal     ->", acc_bal, "| 期望 ≈ 0.77（不是重点，重点是 recall）")
print()
print("TODO1 model_bal2     ->", model_bal2)
print("TODO1 pred_bal2 长度 ->", len(pred_bal2) if pred_bal2 is not None else None, "| 期望 60")
print("TODO1 acc_bal2       ->", acc_bal2, "| 期望 ≈ 0.77")
print()
print("TODO2 no_as_no       ->", no_as_no, "| 期望 17")
print("TODO2 no_as_yes      ->", no_as_yes, "| 期望 4")
print("TODO2 yes_as_no      ->", yes_as_no, "| 期望 10")
print("TODO2 yes_as_yes     ->", yes_as_yes, "| 期望 29")
print("     四格加起来应该 = 60，先自己验证这一点")
print()
print("TODO3 recall_no_2    ->", recall_no_2, "| 期望 ≈ 0.81")
print("TODO3 precision_no_2 ->", precision_no_2, "| 期望 ≈ 0.63")
