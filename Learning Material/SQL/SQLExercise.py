# %% [markdown]
# # Exercise 7
# It is recommended to run this file as a jupyter notebook which will make it easier to display each question seperatly and to view the data using the variable view.

# %%

import mysql.connector as connector
import pandas as pd
import numpy as np

mydb = connector.connect(
    host="localhost",
    username="Benshcha",
    password="XunxuoTable70705",
    database="Employees"
)

myCursor = mydb.cursor()

def ResToDF():
    
    res = pd.DataFrame(myCursor.fetchall(), columns= [col[0] for col in myCursor.description])
    return res


# %%
# 1

myCursor.execute("SELECT * FROM employees")

q1 = ResToDF()
IDs = q1["employee_id"]
print(q1)


# %%
# 2

myCursor.execute("SELECT * FROM employees WHERE first_name LIKE 'a%'\
")

q2 = ResToDF()
print(q2)


# %%
# 3

myCursor.execute("SELECT first_name AS 'First Name', last_name AS 'Last Name', salary FROM employees")

q3 = ResToDF()
q3['salary'] *= 12
print(q3)

# %%
# 4

def printDep(depID):
    myCursor.execute(f"SELECT * FROM employees WHERE department_id = {depID}")
    
    return ResToDF()
    
q4 = printDep(80)
print(q4)

# %%
# 5

myCursor.execute("SELECT * FROM employees ORDER BY first_name ASC")

q5 = ResToDF()
print(q5)

# %%
# 6

myCursor.execute("SELECT * FROM employees WHERE (department_id = 80 OR department_id = 100) AND salary > 1000")

q6 = ResToDF()
print(q6)

# %%
# 7

def printYearlySalRange(n1, n2):
    myCursor.execute(f"SELECT first_name AS 'First Name', last_name AS 'Last Name', salary AS 'Mounthly Salary' FROM employees WHERE salary <= {n2/12} AND salary >= {n1/12}")
    
    return ResToDF()

q7 = printYearlySalRange(0, 100000)
print(q7)

# %%
# 8

myCursor.execute("SELECT * FROM employees")
q8Before = ResToDF()

choclates = ["Milk", "Dark", "White"]

try:
    cmd = "ALTER TABLE employees ADD favorite_choclate VARCHAR(10)"
    myCursor.execute(cmd)
    mydb.commit()
    
except Exception as e:
    print("favorite_choclate already exists")
    
try:
    cmd = "ALTER TABLE employees ADD favorite_number INT(255)"
    myCursor.execute(cmd)
    mydb.commit()
except Exception as e:
    print("favorite_number already exists")

for i, ID in enumerate(IDs):
    newNum = int(np.pi*10**i%10)
    newChoclate = np.random.choice(choclates)
    cmd = f"UPDATE employees SET favorite_choclate = '{newChoclate}', favorite_number = {newNum} WHERE employee_id = {ID}"
    myCursor.execute(cmd)
    
mydb.commit()

myCursor.execute("SELECT * FROM employees")
q8After = ResToDF()
print("Before: ")
print(q8Before)
print("After: ")
print(q8After)
# %%

# 9 
myCursor.execute("SELECT * FROM employees")
q9Before = ResToDF()

myCursor.execute("ALTER TABLE employees DROP favorite_choclate")
mydb.commit()

myCursor.execute("SELECT * FROM employees")
q9After = ResToDF()
print("Before: ")
print(q9Before)
print("After: ")
print(q9After)