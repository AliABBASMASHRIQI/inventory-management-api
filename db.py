from config import host, user, password, database, port
import mysql.connector

connection = mysql.connector.connect(
    host=host,
    port=port,
    user=user,
    password=password,
    database=database
)

print(connection.is_connected())

cursor = connection.cursor()