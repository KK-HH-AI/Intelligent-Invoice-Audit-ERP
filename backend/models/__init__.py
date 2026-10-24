"""实体层：每张（组）表一个文件，只做单表读写，不含业务规则。

纪律：
- 只允许 import db（拿连接）与标准库，不互相 import；
- 需要"跨表拼数据"时往上交给 services 层组装；
- 所有函数返回 sqlite3.Row / list[Row] 或 lastrowid，不自行转 JSON。
"""
