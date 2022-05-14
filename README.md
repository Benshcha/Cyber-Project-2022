# Cyber-Project-2022 Gal Ben-Shach

## Documentation

Documentation is inside [/docs/documentation](https://benshcha.github.io/Cyber-Project-2022/docs/documentation/main.html) folder.  
It is reccomended to run the command `python -m pydoc -b` inside the related enviorment in order to read the documentation properly

## Running the server

To run the server, all the python related packages should be installed in the interpreted and the file [main.py](main.py) should be run.

There should be a json file called `dbconfig.json` with the configiration of the database. For example:

```json
{
    "host": "localhost",
    "username": "Benshcha",
    "password": "Super secure and secret password",
    "database": "CyberProject2022",
    "pool_name": "updateNotebooks",
    "autocommit": "True"
}
```

## Closing the server safely

To close the server safely it is very important to use the command `exit` inside the console in order to save the database changes to the corresponding json files.
