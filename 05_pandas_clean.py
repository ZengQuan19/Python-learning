# ============================================================
# 技能 5 / 7：清洗与编码 —— 把表变成模型能吃的数字
# 用法：右键 -> Run '05_pandas_clean'
# ============================================================

import pandas as pd

df = pd.read_csv("students.csv")
new_df = pd.read_csv("students_new.csv")

# ------------------------------------------------------------
# 第一部分：热身（不用改，直接运行，对照输出理解）
# ------------------------------------------------------------

print("=== 1. 缺失值的两条路：删行 vs 填值 ===")
print("原始行数：", len(df))

print("dropna() 删掉有空的行后：", len(df.dropna()))

filled = df.copy()
filled["score"] = filled["score"].fillna(filled["score"].median())
print("填上中位数之后，非空个数：", filled["score"].count())
print("填进去的中位数是：", df["score"].median())
print()

print("=== 2. 为什么必须编码：模型不认文字 ===")
print("city 列出现了哪些值：", df["city"].unique())
print()

print("=== 3. One-Hot 编码：一列拆成好几列 ===")
encoded = pd.get_dummies(df, columns=["city"])
print(encoded.head())
print("编码后的列名：", list(encoded.columns))
print()

print("=== 4. 列对齐陷阱：新旧数据编码后列数不一样 ===")
new_encoded = pd.get_dummies(new_df, columns=["city"])
print("训练集编码后列数：", encoded.shape[1])
print("新数据编码后列数：", new_encoded.shape[1])
print("   -> 差在哪？看看两边的列名")
print()

print("=== 5. 修复：把新数据的列对齐到训练集 ===")
new_aligned = new_encoded.reindex(columns=encoded.columns, fill_value=0)
print("对齐后列数：", new_aligned.shape[1])
print()


# ------------------------------------------------------------
# 第二部分：过关任务（在这里作答）
# ------------------------------------------------------------

# TODO 1：把 df 的 score 缺失值用"中位数"填上，结果存给 filled_df
#         要求：不要动原始 df（先 df.copy()）
filled_df = df.copy()
filled_df["score"] = filled_df["score"].fillna(filled_df["score"].median())

# TODO 2：对 filled_df 做 One-Hot 编码（处理 city 列），存给 encoded_df
encoded_df = pd.get_dummies(filled_df, columns=["city"])

# TODO 3：把 new_df 也做 One-Hot，再对齐到 encoded_df 的列，存给 new_aligned
#         要求：new_df 里没有的列要补 0
new_encoded_df = pd.get_dummies(new_df, columns=["city"])
new_aligned = new_encoded_df.reindex(columns=encoded_df.columns, fill_value=0)

# ------------------------------------------------------------
# 第三部分：自检区（不要改）
# ------------------------------------------------------------
print("===== 自检 =====")
print("filled_df 还有缺失吗 ->", filled_df["score"].isnull().any(), "| 期望 False")
print("filled_df 非空个数   ->", filled_df["score"].count(), "| 期望 10"
print("原始 df 被污染了吗   ->", df["score"].isnull().any(), "| 期望 True（原始表要保持原样）")
print("encoded_df 列数      ->", encoded_df.shape[1], "| 期望 7")
print("new_aligned 列数     ->", new_aligned.shape[1], "| 期望 7")
print("new_aligned 的列名   ->")
print(list(new_aligned.columns))
