

import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host="team-auth-db.cdak644ym5fe.ap-southeast-2.rds.amazonaws.com",
    database="postgres",
    user="ZULU",
    password="SENG2011zulu",
    cursor_factory=RealDictCursor,
)

cur = conn.cursor()
cur.execute("SELECT * FROM users;")
rows = cur.fetchall()

for row in rows:
    print(row)

conn.close()
