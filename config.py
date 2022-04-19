"""
File for sharing global variables
"""

# logger:
from modules import myLogger
logger = myLogger("mainLogger")

# json files for db
jsonFiles = {'users': {"path": 'Protected/UsersLoginData.json'}, 'notebooks': {"path": "Protected/Notebooks/NotebooksList.json", "without": "code"}}

# silent log
silentLog = False
