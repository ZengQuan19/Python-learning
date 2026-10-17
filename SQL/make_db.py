# ============================================================
# 练习数据库生成器（不用改，需要重建数据时再跑一次）
# 运行：右键 -> Run 'make_db'
# 产物：同目录下的 practice.db
#
# 为什么要有这个文件：
#   万一你把数据玩坏了（DELETE 掉一张表之类），跑一下就能复原。
# ============================================================

import random
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("practice.db")

users = [
    (1, "张伟", "北京", "2024-01-05", 28),
    (2, "王芳", "上海", "2024-01-18", 34),
    (3, "李娜", "北京", "2024-02-02", 22),
    (4, "刘强", "广州", "2024-02-20", 45),
    (5, "陈静", "上海", "2024-03-11", 31),
    (6, "杨洋", "深圳", "2024-03-25", 26),
    (7, "赵敏", "北京", "2024-04-08", 39),
    (8, "周杰", None, "2024-04-22", 24),        # city 故意留空，后面讲 NULL 用
    (9, "吴磊", "成都", "2024-05-06", 52),
    (10, "郑爽", "上海", "2024-05-19", 29),
    (11, "孙悦", "深圳", "2024-06-01", 33),
    (12, "马丽", "北京", "2024-06-15", 41),     # 故意不给订单，后面讲 LEFT JOIN 用
]

products = [
    (101, "机械键盘", 399.0, "数码"),
    (102, "无线鼠标", 129.0, "数码"),
    (103, "显示器", 1099.0, "数码"),
    (104, "保温杯", 89.0, "生活"),
    (105, "台灯", 159.0, "家居"),
    (106, "跑鞋", 499.0, "运动"),
    (107, "背包", 259.0, "运动"),
    (108, "笔记本", 19.9, "文具"),              # 故意从没被买过，后面讲 LEFT JOIN 用
]

# 订单用固定种子生成，保证每次跑出来的数据完全一样（可复现很重要）
random.seed(42)
price = {p[0]: p[2] for p in products}
statuses = ["paid", "paid", "paid", "paid", "pending", "cancelled", "refunded"]
orders = []
for order_id in range(1, 41):
    user_id = random.choice(range(1, 12))       # 12 号用户永远没有订单
    product_id = random.choice([101, 102, 103, 104, 105, 106, 107])   # 108 永远没被买
    qty = random.choice([1, 1, 2, 3])
    amount = round(price[product_id] * qty, 2)
    status = random.choice(statuses)
    month = random.choice(["07", "08", "09", "10", "11", "12"])
    day = random.randint(1, 28)
    orders.append((order_id, user_id, product_id, qty, amount, status, f"2024-{month}-{day:02d}"))

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.executescript(
    """
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS products;
    DROP TABLE IF EXISTS users;

    CREATE TABLE users (
        user_id     INTEGER PRIMARY KEY,
        name        TEXT    NOT NULL,
        city        TEXT,
        signup_date TEXT,
        age         INTEGER
    );

    CREATE TABLE products (
        product_id   INTEGER PRIMARY KEY,
        product_name TEXT    NOT NULL,
        price        REAL,
        category     TEXT
    );

    CREATE TABLE orders (
        order_id   INTEGER PRIMARY KEY,
        user_id    INTEGER,
        product_id INTEGER,
        quantity   INTEGER,
        amount     REAL,
        status     TEXT,
        order_date TEXT
    );
    """
)
cur.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?)", users)
cur.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products)
cur.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)", orders)
conn.commit()

print("数据库已重建：", DB_PATH)
for t in ("users", "products", "orders"):
    n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t:<9} {n} 行")
conn.close()
