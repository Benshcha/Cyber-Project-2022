import pyodbc
import sqlite3 as sq3
import mysql.connector


# access to sqlite3 database
def sql3file():
    conn = sq3.connect(r'd:\ytest.db')  # create DB if not exist otherwise connects to it.
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS customers (name VARCHAR(255), address VARCHAR(255))")

    sql_command = "SELECT * FROM Table1"
    cursor.execute(sql_command)
    data = cursor.fetchall()
    for d in data:
        print(d)

    conn.close()

    conn = sq3.connect('testDB1.db')
    cursor = conn.cursor()
    sql_command = "DROP TABLE IF EXISTS test"
    cursor.execute(sql_command)
    cursor.execute("CREATE TABLE IF NOT EXISTS test (name CHAR, age INTEGER, location CHAR)")
    # sql_command = "DELETE FROM test"  # Deletes all table data
    # cursor.execute(sql_command)

    sql_command = "INSERT INTO test VALUES('YOSSI',34, 'Tel-Aviv')"
    cursor.execute(sql_command)
    sql_command = "INSERT INTO test VALUES('JOE',54, 'Ber-Seva')"
    cursor.execute(sql_command)
    sql_command = "INSERT INTO test VALUES('Jerry',60, 'Jerusalem')"
    cursor.execute(sql_command)
    sql_command = "INSERT INTO test VALUES('Michal',35, 'Pardesiya')"
    cursor.execute(sql_command)

    conn.commit()  # writes data to database file


# access to MS Access database
def access_file():
    conn_str = r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=d:\testdb.accdb'
    print(pyodbc.drivers())
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    found = False
    xx = cursor.tables(tableType='TABLE')
    for i in xx:
        print(i.table_name)
        if 'Table2' in i:
            found = True

    if not found:
        cursor.execute("create table Table2(one varchar(15), shares integer)")
        cursor.commit()
    cursor.execute("select * from Table1")
    data = cursor.fetchall()

    for d in data:
        print(d)


mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="5725",
    database="test"
)


def mysql_access():
    mycursor = mydb.cursor(buffered=True)
    # mycursor.execute("SHOW DATABASES")
    # for x in mycursor:
    #     print(x)

    mycursor.execute("CREATE TABLE IF NOT EXISTS customers (name VARCHAR(255), address VARCHAR(255))")
    mycursor.execute("DELETE FROM customers")
    mydb.commit()
    sql = "INSERT INTO customers (name, address) VALUES (%s, %s)"
    val = ("John", "Highway 21")
    mycursor.execute(sql, val)

    sql = "INSERT INTO customers (name, address) VALUES (%s, %s)"
    val = ("Yoram", "Hadarim 72")
    mycursor.execute(sql, val)

    sql = "INSERT INTO customers (name, address) VALUES (%s, %s)"
    val = ("Michal", "Arbel 4")
    mycursor.execute(sql, val)

    mydb.commit()

    mycursor.execute("SELECT * FROM customers")
    print(mycursor.rowcount, "record inserted.")
    results = mycursor.fetchall()

    for x in results:
        print(x)


if __name__ == '__main__':
    print('SQL-LITE')
    sql3file()
    print()
    print('MS ACCESS')
    access_file()
    print()
    print('MYSQL')
    mysql_access()
