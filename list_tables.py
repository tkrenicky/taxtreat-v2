import sqlite3

conn = sqlite3.connect(r"data\processed\taxtreat_cz.sqlite")

for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print(row[0])