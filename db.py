from config import host,password,user,database
import mysql.connector

connection = mysql.connector.connect(
    host = host,
    user = user,
    password = password,
    database = database
)
print(connection.is_connected())

cursor = connection.cursor()
