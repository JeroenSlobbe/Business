# pip install cbsodata
# pip install ecbdata


import sqlite3
from datetime import date, datetime, timedelta
import time
import cbsodata
from ecbdata import ecbdata

timestamp = date.today()


# You can explore a CBS dataset, by entering keywords on: https://opendata.cbs.nl/#/CBS/nl/. When clicking the url, the id (?????ned) will become visible.
# ECB data can be explored via: https://data.ecb.europa.eu/help/browse-data-dataset

def getECBInterestRates():
    df = ecbdata.get_series('FM.B.U2.EUR.4F.KR.MRR_FR.LEV')
    ECBIR = (df.iloc[-1])['OBS_VALUE']
    print("ECB interest rate was: ", ECBIR, "% on: ",(df.iloc[-1])['TIME_PERIOD'],". Based on data from the ecbdata API")
    return ECBIR

def getInflation():
    info = cbsodata.get_info('70936ned')
    data = cbsodata.get_data('70936ned')
    last_entry = data[-2] 
    inflation = last_entry['JaarmutatieCPI_1']
    print("Inflation was:", inflation, "% for: ", last_entry['Perioden']   ,". Based on data from: ", info['ShortTitle'])
    return inflation
   
def getUnemployment():   
    info = cbsodata.get_info('85224NED')
    data = cbsodata.get_data('85224NED')
    last_entry = data[-2] 
    unemployment = last_entry['Werkloosheidspercentage_25']
    print("Unemployment was:", unemployment, "% for: ", last_entry['Perioden']   ,". Based on data from: ", info['ShortTitle'])
    return unemployment

def getConsumerConfidence():
    # Note: value between -100 and +100: https://www.cbs.nl/nl-nl/nieuws/2024/47/consumenten-negatiever-in-november
    info = cbsodata.get_info('83693NED')
    data = cbsodata.get_data('83693NED')
    last_entry = data[-2] 
    consumerConfidence = last_entry['Consumentenvertrouwen_1']
    print("Consumer confidence was:", consumerConfidence, "% for: ", last_entry['Perioden']   ,". Based on data from: ", info['ShortTitle'])
    return consumerConfidence   
    
    
    

# Main program
inflation = getInflation()
unemployment = getUnemployment()
consumerConfidence = getConsumerConfidence()
ECBIR = getECBInterestRates()

# Store in Database

db_path = "ScreeningsDB.db"  # Replace with your SQLite database path
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

insert_query = "INSERT INTO economyhistory (date, inflation, ECBInterest, NL_Unemployment, NL_ConsumerConfience)VALUES (?, ?, ?, ?, ?)"
cursor.execute(insert_query, (timestamp, inflation, ECBIR, unemployment, consumerConfidence))
conn.commit()
print("Data successfully inserted into economyhistory.")
conn.close()
