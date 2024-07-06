import pymysql

connection = pymysql.connect(host='localhost',
                             user='root',
                             password='',
                             database='liquidmind',
                             port=3306,
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

try:
    with connection.cursor() as cursor:
        # Example query
        cursor.execute("SELECT VERSION()")
        result = cursor.fetchone()
        print(result)
finally:
    connection.close()
