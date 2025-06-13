import sqlite3
import re
from Config.config import *

# Database location
dbLocation = Config.dbLocation

# ************************** DATA FETCHING ************************** #  

def simple_query(query):
    connection = sqlite3.connect(dbLocation)
    cursor = connection.cursor()
    cursor.execute(query)
    data = cursor.fetchall()  
    connection.close()   
    return data

def simple_query_rowfactory(query):
    connection = sqlite3.connect(dbLocation)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute(query)
    data = cursor.fetchall()  
    connection.close()   
    return data

    
# Used for queries with limit 1
def simple_query_one(query):
    connection = sqlite3.connect(dbLocation)
    cursor = connection.cursor()
    cursor.execute(query)
    data = cursor.fetchone()  
    connection.close()   
    return data
    
# Used for selections based on an ID
def simple_dynamic_query_INT(query, myID):
    connection = sqlite3.connect(dbLocation)
    cursor = connection.cursor()
    filteredID = int(myID)
    cursor.execute(query, (filteredID,))
    data = cursor.fetchall()  
    connection.close()   
    return data
    
# Used for selections based on an ID with a limit of one
def simple_dynamic_query_INT_one(query, myID):
    connection = sqlite3.connect(dbLocation)
    cursor = connection.cursor()
    filteredID = int(myID)
    cursor.execute(query, (filteredID,))
    data = cursor.fetchone()  
    connection.close()   
    return data
    
# Used for selections based on an ID with a limit of one
def simple_dynamic_query_rowfactory_INT_one(query, myID):
    connection = sqlite3.connect(dbLocation)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    filteredID = int(myID)
    cursor.execute(query, (filteredID,))
    data = cursor.fetchone()  
    connection.close()   
    return data
    
# Used for selections based on a STRING
def simple_dynamic_query_STRING_one(query, myInput, securityFilter):
    if re.match(securityFilter, myInput):
        connection = sqlite3.connect(dbLocation)
        cursor = connection.cursor()
        cursor.execute(query, (myInput,))
        data = cursor.fetchone()  
        connection.close()
        return data
    else:
        print("Security violation")
        return None

# Used for selections based on two STRINGS
def two_dynamic_query_STRING_one(query, myInputs, securityFilters):
    if len(myInputs) == len(securityFilters):
        queryAllowed = True
        for index, myInput in enumerate(myInputs):
            if not re.match(securityFilters[index], str(myInputs[index])):
                queryAllowed = False
                print("Security violation", query, "on: ", index, "out of: ", myInputs)
                return False
        if(queryAllowed):
            connection = sqlite3.connect(dbLocation)
            cursor = connection.cursor()
            cursor.execute(query, myInputs)
            data = cursor.fetchone()
            connection.close()
            return data            
    else:
        print("All inputs should have a security filter")
        
# ************************** DATA REMOVAL ************************** #    
# Used for selections based on an ID
def simple_dynamic_query_DELETE_INT(query, myID):
    connection = sqlite3.connect(dbLocation)
    cursor = connection.cursor()
    filteredID = int(myID)
    cursor.execute(query, (filteredID,))
    connection.commit()
    connection.close()   

# ************************** INSERT DATA ************************** #  

def insert_data(query, inputs, securityFilters):
    queryAllowed = True
    
    if len(inputs) == len(securityFilters):
        for index, myInput in enumerate(inputs):
            if not re.match(securityFilters[index], str(inputs[index])):
                queryAllowed = False
                print("Security violation", query, "on: ", index, "out of: ", inputs)
                return False
        if(queryAllowed):
            connection = sqlite3.connect(dbLocation)
            cursor = connection.cursor()
            cursor.execute(query, inputs)
            connection.commit()
            connection.close()  
    else:
        print("All inputs should have a security filter")

# ************************** UPDATE DATA ************************** #  

def update_data(query, inputs, securityFilters):
    queryAllowed = True
    
    if len(inputs) == len(securityFilters):
        for index, myInput in enumerate(inputs):
            if not re.match(securityFilters[index], str(inputs[index])):
                queryAllowed = False
                print("Security violation")
                return False
        if(queryAllowed):
            connection = sqlite3.connect(dbLocation)
            cursor = connection.cursor()
            cursor.execute(query, inputs)
            connection.commit()
            connection.close()  
    else:
        print("All inputs should have a security filter")