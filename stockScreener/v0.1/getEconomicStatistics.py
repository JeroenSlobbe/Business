# pip install cbsodata
# pip install ecbdata


import sqlite3
from datetime import date, datetime, timedelta
import time
import cbsodata
from ecbdata import ecbdata
import yfinance as yf

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
    
def getEURUSDExchangeRate():
    ticker = "EURUSD=X"
    data = yf.Ticker(ticker)
    # Get the current exchange rate (latest close price)
    exchange_rate = data.history(period="1d")['Close'].iloc[-1]
    print("USD to EUR exchange rate:", exchange_rate, "e.g. 1 euro is: ", exchange_rate, " dollar, based on yahoofinance")
    return exchange_rate

def getGDPGrowth(): 
    info = cbsodata.get_info('85880NED')
    data = cbsodata.get_data('85880NED')
    dataFiltered = []
    gdpGrowth = ""
    for x in data:
        if x['SoortMutaties'] == 'Volume, t.o.v. zelfde periode vorig jaar':
            dataFiltered.append(x)
    last_entry = dataFiltered[-1]

    gdpGrowth = last_entry['BbpGecorrigeerdVoorWerkdageneffecten_3']
    print("GDP Growth:", gdpGrowth, "% for: ", last_entry['Perioden']   ,". Based on data from: ", info['Title'])
    return gdpGrowth

def getRetailSales():
    info = cbsodata.get_info('83867NED')
    data = cbsodata.get_data('83867NED')
    last_entry = data[-1] 
    retailSales = last_entry['OmzetontwikkelingTOVEenJaarEerder_2']
    print("Retail sales compared to last year was:", retailSales, "% for: ", last_entry['Perioden']   ,". Based on data from: ", info['ShortTitle'])
    return retailSales 

def getProduction():
    info = cbsodata.get_info('85806NED')
    data = cbsodata.get_data('85806NED')
    dataFiltered =[]
    
    for x in data:
        if x['BedrijfstakkenBranchesSBI2008'] == 'C Industrie':
            dataFiltered.append(x)
    last_entry = dataFiltered[-1] 
    production = last_entry['KalendergecorrigeerdeProductie_14']
    print("Industrial production compared to last year was:", production, "% for: ", last_entry['Perioden']   ,". Based on data from: ", info['ShortTitle'])
    return production 

def getBankrupcies():
    info = cbsodata.get_info('82242NED')
    data = cbsodata.get_data('82242NED')
    last_month_entry = data[-2]
    last_entry = data[-1] 
    last_month_bankrupcies = last_month_entry['UitgesprokenFaillissementen_1']
    this_month_bankrupcies = last_entry['UitgesprokenFaillissementen_1']
    bankrupcies = round((((this_month_bankrupcies - last_month_bankrupcies) / last_month_bankrupcies) *100),2)
    print("NL bankrupcies:", bankrupcies, "% for: ", last_entry['Perioden']   ,". Based on data from: ", info['ShortTitle'])
    return bankrupcies   
    
# Main program
inflation = getInflation()
unemployment = getUnemployment()
consumerConfidence = getConsumerConfidence()
ECBIR = getECBInterestRates()
EUR_USD_ExchangeRate = getEURUSDExchangeRate()
GDPGrowth = getGDPGrowth()
NL_RetailSales = getRetailSales()
NL_IndustrialProduction = getProduction()
NL_Bankrupcies = getBankrupcies()

# Store in Database

db_path = "ScreeningsDB.db"  # Replace with your SQLite database path
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

insert_query = "INSERT INTO economyhistory (date, inflation, ECBInterest, NL_Unemployment, NL_ConsumerConfidence, EUR_USD_ExchangeRate,NL_GDPGrowth, NL_RetailSales, NL_IndustrialProduction,NL_Bankrupcies)VALUES (?, ?, ?, ?, ?,?,?,?,?,?)"
cursor.execute(insert_query, (timestamp, inflation, ECBIR, unemployment, consumerConfidence, EUR_USD_ExchangeRate,GDPGrowth,NL_RetailSales,NL_IndustrialProduction,NL_Bankrupcies))
conn.commit()
print("Data successfully inserted into economyhistory.")
conn.close()

