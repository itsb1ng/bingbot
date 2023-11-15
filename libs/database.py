import sqlite3

dbTables = {"giveaway": "giveaway", "servers": "serverdata", "economy": "userdata"}

def connect_db(dbname):
    if dbname == "giveaway":
        return sqlite3.connect(f"./data/giveaway.db")
    elif dbname == "servers":
        return sqlite3.connect(f"./data/servers.db")
    else:
        return sqlite3.connect(f"./data/economy.db")

def get_db_data(dbname):
    conn = connect_db(dbname)
    cursor = conn.cursor()
    return conn, cursor

def db_interact(dbname, query, commitData):
    dbData = get_db_data(dbname)
    conn = dbData[0]
    cursor = dbData[1]

    if commitData:
        cursor.execute(query)
        conn.commit()
    else:
        return cursor.execute(query).fetchall()

    if commitData:
        conn.commit()

    cursor.close()
    conn.close()

def insert_query(dbname, values):
    db_interact(dbname, f'''INSERT INTO {dbTables[dbname]} VALUES {values}''', True)

def return_table_data(dbname):
    return db_interact(dbname, f'''SELECT * FROM {dbTables[dbname]}''', False)

def return_row_data(dbname, condition, value):
    return db_interact(dbname, f'''SELECT * FROM {dbTables[dbname]} WHERE {condition}={value}''', False)

def update_row_data(dbname, newColumn, newValue, conditionColumn, conditionValue):
    dbData = get_db_data(dbname)
    conn = dbData[0]
    cursor = dbData[1]
    
    update_query = f"UPDATE {dbTables[dbname]} SET {newColumn} = ? WHERE {conditionColumn} = ?"
    cursor.execute(update_query, (newValue, conditionValue))

    conn.commit()

    cursor.close()
    conn.close()

def list_to_string(inList):
    return ', '.join(inList)

def string_to_list(inString):
    return inString.split(', ')

def dict_data_return(dictionary):
    return tuple(dictionary.values())

def format_data(dbname, tuple):
    if dbname == "giveaway": 
        return dict({"msgID": tuple[0][0], "channelID": tuple[0][1], "prize": tuple[0][2], "description": tuple[0][3], "creator": tuple[0][4], "winners": tuple[0][5], "end": tuple[0][6], "entries": tuple[0][7], "completed": tuple[0][8]})
    elif dbname == "servers":
        return dict({"guildID": tuple[0][0], "logs": tuple[0][1], "defaultRole": tuple[0][2]})
    else: 
        return dict({"userID": tuple[0][0], "wallet": tuple[0][1], "bank": tuple[0][2], "balance": tuple[0][3], "spent": tuple[0][4], "depoTime": tuple[0][5], "maxAFK": tuple[0][6], "lastAFK": tuple[0][7], "robSuccess": tuple[0][8], "stealPercent": tuple[0][9], "lastRob": tuple[0][10]})