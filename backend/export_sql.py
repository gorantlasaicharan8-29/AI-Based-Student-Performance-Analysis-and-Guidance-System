import pymysql
import os

MYSQL_USER = "root"
MYSQL_PASSWORD = "Root@2026#"
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_DB = "student_performance_db"

conn = pymysql.connect(
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DB,
    charset="utf8mb4"
)
cursor = conn.cursor()

tables = [
    "users", "students", "subjects", "marks",
    "units", "topics", "assignments", "submissions",
    "predictions", "notifications"
]

sql_lines = [
    "-- MySQL Database Dump",
    "-- AI-Based Student Performance Analysis and Guidance System",
    f"-- Database: {MYSQL_DB}",
    "-- ------------------------------------------------------\n",
    "SET FOREIGN_KEY_CHECKS = 0;\n"
]

for table in tables:
    cursor.execute(f"SHOW CREATE TABLE `{table}`")
    create_stmt = cursor.fetchone()[1]
    sql_lines.append(f"DROP TABLE IF EXISTS `{table}`;")
    sql_lines.append(f"{create_stmt};\n")

    cursor.execute(f"SELECT * FROM `{table}`")
    rows = cursor.fetchall()
    if rows:
        cursor.execute(f"SHOW COLUMNS FROM `{table}`")
        cols = [col[0] for col in cursor.fetchall()]
        col_names = ", ".join([f"`{c}`" for c in cols])

        vals_list = []
        for r in rows:
            formatted_vals = []
            for val in r:
                if val is None:
                    formatted_vals.append("NULL")
                elif isinstance(val, (int, float)):
                    formatted_vals.append(str(val))
                else:
                    escaped = str(val).replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")
                    formatted_vals.append(f"'{escaped}'")
            vals_list.append("(" + ", ".join(formatted_vals) + ")")

        insert_sql = f"INSERT INTO `{table}` ({col_names}) VALUES\n" + ",\n".join(vals_list) + ";\n"
        sql_lines.append(insert_sql)

sql_lines.append("SET FOREIGN_KEY_CHECKS = 1;\n")

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database_dump.sql")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(sql_lines))

print("[OK] database_dump.sql created successfully in backend/ folder!")
