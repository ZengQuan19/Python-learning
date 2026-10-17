# ============================================================
# 技能 3 / 7：pandas 入门 —— 把表格读进来、看清楚
# 用法：右键 -> Run '03_pandas'
# ============================================================

import pandas as pd

# ------------------------------------------------------------
# 第一部分：热身（不用改，直接运行，逐段看输出）
# ------------------------------------------------------------
df = pd.read_csv("students.csv")

print("=== shape：几行几列 ===")
print(df.shape)
print()

print("=== head()：前 5 行 ===")
print(df.head())
print()

print("=== info()：每列的类型 + 非空个数 ===")
df.info()
print()

print("=== describe()：数值列的统计 ===")
print(df.describe())
print()

print("=== 每列有几个缺失值 ===")
print(df.isnull().sum())
print()

print("=== 取一列出来看 ===")
print(df["score"])
print()


# ------------------------------------------------------------
# 第二部分：过关任务（在这里作答）
# ------------------------------------------------------------
# 提示：很多东西你已经在技能 2 学过了。
#      df["score"] 取出来的那一列，用法跟 NumPy 数组几乎一样。

# TODO 1：这个表有几行、几列？分别赋值给 row_count 和 col_count
#         提示：df.shape 会一次给出两个数，可以像 row_count, col_count = ... 这样拆开
row_count = df.shape[0]
col_count = df.shape[1]

# TODO 2：哪一列有缺失值？填列名（字符串）；缺了几个？填整数
missing = df.isnull().sum()
missing = missing[missing > 0]
missing_col = missing.index[0]
missing_count =missing.values[0]

# TODO 3：score 这一列的平均分是多少？
#         提示：你已经知道怎么求平均了，df["score"] 就是一个数组
score_mean = df["score"].mean()


# ------------------------------------------------------------
# 第三部分：自检区（不要改）
# ------------------------------------------------------------
print("===== 自检 =====")
print("行数       ->", row_count, "| 期望 10")
print("列数       ->", col_count, "| 期望 5")
print("有缺失的列 ->", missing_col, "| 期望 score")
print("缺失个数   ->", missing_count, "| 期望 2")
print("score 平均 ->", score_mean, "| 期望 77.25")
