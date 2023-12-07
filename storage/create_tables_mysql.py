import mysql.connector

# Update these values with your specific configuration
db_config = {
    'host': 'ec2-44-210-173-19.compute-1.amazonaws.com',
    'user': 'richard',
    'password': '3855',
    'database': 'acit',
    'port': 3306
}

db_conn = mysql.connector.connect(**db_config)
db_cursor = db_conn.cursor()

# Create table for InfectedInfo
db_cursor.execute('''
CREATE TABLE report_covid
(id INT NOT NULL AUTO_INCREMENT,
patient_id INTEGER NOT NULL,
date_created DATETIME NOT NULL,
date_handwritten DATETIME NOT NULL DEFAULT '2023-10-20 00:00:00', 
vaccinated_status INTEGER NOT NULL,
city VARCHAR(250) NOT NULL,
age INTEGER NOT NULL,
PRIMARY KEY (id))
''')

# Create table for RecoveryInfo
db_cursor.execute('''
CREATE TABLE report_recovery
(id INT NOT NULL AUTO_INCREMENT,
patient_id VARCHAR(250) NOT NULL,
recovery_status VARCHAR(250) NOT NULL,
date_created DATETIME NOT NULL,
date_handwritten DATETIME NOT NULL DEFAULT '2023-10-20 00:00:00', 
hospital_visit VARCHAR(3) NOT NULL,
PRIMARY KEY (id))
''')

db_conn.commit()
db_conn.close()
