import MySQLdb

conn = MySQLdb.connect(host='localhost', user='root', passwd='Harita@1234', db='dietmate_db')
cur = conn.cursor()
print('SCHEMA')
cur.execute('SHOW COLUMNS FROM user_meal_progress')
for row in cur.fetchall():
    print(row)
print('---')
q1 = 'SELECT COUNT(DISTINCT log_date) FROM user_meal_progress WHERE user_id=%s AND completed=TRUE AND log_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)'
q2 = 'SELECT COUNT(DISTINCT date) FROM user_meal_progress WHERE user_id=%s AND completed=TRUE AND date >= DATE_SUB(NOW(), INTERVAL 30 DAY)'
for idx, q in enumerate((q1, q2), 1):
    try:
        cur.execute(q, (1,))
        print(f'Q{idx} OK', cur.fetchone())
    except Exception as e:
        print(f'Q{idx} ERROR', e)
cur.close()
conn.close()
