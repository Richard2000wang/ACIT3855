import mysql.connector

db_config = {
    'host': 'ec2-44-210-173-19.compute-1.amazonaws.com',
    'user': 'richard',
    'password': '3855',
    'database': 'acit',
    'port': 3306
}

db_conn = mysql.connector.connect(**db_config)
db_cursor = db_conn.cursor()

# Drop table for InfectedInfo
db_cursor.execute('DROP TABLE IF EXISTS report_covid')

# Drop table for RecoveryInfo
db_cursor.execute('DROP TABLE IF EXISTS report_recovery')

db_conn.commit()
db_conn.close()
