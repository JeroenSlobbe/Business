from datetime import date, datetime, timedelta
import cbsodata
from ecbdata import ecbdata
import yfinance as yf
import numpy as np
import requests
import pandas as pd
from io import StringIO
from Logic.database import *
from Config.config import *
import xml.etree.ElementTree as ET
from datetime import datetime

# OECD function
def getEUClie():
    EUBig4CLI = 0
    try:
        now = datetime.now()
        year = now.year
        month = now.month - 1
        if month == 0:
            month = 12
            year -= 1
        period = f"{year}-{month:02d}"

        # Build URL
        url = (
            "https://sdmx.oecd.org/public/rest/data/"
            "OECD.SDD.STES,DSD_STES@DF_CLI,/.M.LI...AA...H"
            f"?startPeriod={period}&dimensionAtObservation=AllDimensions"
        )

        # Fetch and parse XML
        response = requests.get(url)
        root = ET.fromstring(response.content)

        # Define namespaces
        ns = {
            "generic": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic",
            "message": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
        }

        # Search for matching Obs
        for obs in root.findall(".//generic:Obs", ns):
            key = obs.find("generic:ObsKey", ns)
            values = {v.attrib["id"]: v.attrib["value"] for v in key.findall("generic:Value", ns)}
            if values.get("REF_AREA") == "G4E" and values.get("TIME_PERIOD") == period:
                obs_value = obs.find("generic:ObsValue", ns)
                EUBig4CLI = obs_value.attrib['value']

    except Exception as e:
        print("[!] Couldn't obtain the CLI from the OECD")
        
    return EUBig4CLI


def getECBInterestRates():
    df = ecbdata.get_series('FM.B.U2.EUR.4F.KR.MRR_FR.LEV')
    return (df.iloc[-1])['OBS_VALUE']

def getInflation():
    data = cbsodata.get_data('70936ned')
    return data[-2]['JaarmutatieCPI_1']

def getUnemployment():
    data = cbsodata.get_data('85224NED')
    return data[-2]['Werkloosheidspercentage_25']

def getConsumerConfidence():
    data = cbsodata.get_data('83693NED')
    return data[-2]['Consumentenvertrouwen_1']

def getEURUSDExchangeRate():
    ticker = "EURUSD=X"
    data = yf.Ticker(ticker)
    return data.history(period="1d")['Close'].iloc[-1]

def getGDPGrowth():
    data = cbsodata.get_data('85880NED')
    volume_entries = [x for x in data if 'Volume' in x['SoortMutaties']]
    kwartaal_entries = [x for x in volume_entries if 'kwartaal' in x['Perioden']]
    last_kwartaal_entry = kwartaal_entries[-1]
    return last_kwartaal_entry['BrutoBinnenlandsProduct_2']

def getRetailSales():
    data = cbsodata.get_data('83867NED')
    return data[-1]['OmzetontwikkelingTOVEenJaarEerder_2']

def getProduction():
    data = cbsodata.get_data('85806NED')
    dataFiltered = [x for x in data if x['BedrijfstakkenBranchesSBI2008'] == 'C Industrie']
    return dataFiltered[-1]['KalendergecorrigeerdeProductie_14']

def getBankrupcies():
    data = cbsodata.get_data('82242NED')
    last_month_entry = data[-2]
    last_entry = data[-1]
    return round((((last_entry['UitgesprokenFaillissementen_1'] - last_month_entry['UitgesprokenFaillissementen_1']) / last_month_entry['UitgesprokenFaillissementen_1']) * 100), 2)

def fetch_and_store_economic_data():
    timestamp = date.today()
    inflation = getInflation()
    unemployment = getUnemployment()
    consumerConfidence = getConsumerConfidence()
    ECBIR = getECBInterestRates()
    EUR_USD_ExchangeRate = getEURUSDExchangeRate()
    GDPGrowth = getGDPGrowth()
    NL_RetailSales = getRetailSales()
    NL_IndustrialProduction = getProduction()
    NL_Bankrupcies = getBankrupcies()
    EUBig4CLI = getEUClie()

    query = "INSERT INTO economyhistory (date, inflation, ECBInterest, NL_Unemployment, NL_ConsumerConfidence, EUR_USD_ExchangeRate, NL_GDPGrowth, NL_RetailSales, NL_IndustrialProduction, NL_Bankrupcies, EU_CLI) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    inputs = [timestamp, inflation, ECBIR, unemployment, consumerConfidence, EUR_USD_ExchangeRate, GDPGrowth, NL_RetailSales, NL_IndustrialProduction, NL_Bankrupcies, EUBig4CLI]
    securityFilters = [r'^\d{4}-\d{2}-\d{2}$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$']
    insert_data(query, inputs, securityFilters)


def computeExpectedDividends(ticker):
    stock_id_query = "SELECT id FROM Stocks WHERE ticker = ?"
    # Assume that: a ticker symbol is not longer than 5 characters, has a normal alphabet and no special symbols: https://en.wikipedia.org/wiki/Ticker_symbol
    stock_id_result = simple_dynamic_query_STRING_one(stock_id_query, ticker, r'^[A-Za-z0-9]{1,20}$')

    if not stock_id_result:
        print("Couldn't find ticker: ", ticker)
    else:
        query = "SELECT 1 FROM dividendExpectations WHERE stockID = ? LIMIT 1"
        allreadyExist = simple_dynamic_query_INT_one(query, int(stock_id_result[0]))
        query = "SELECT exchange from stocks WHERE id = ?"
        exchange = simple_dynamic_query_INT_one(query, int(stock_id_result[0]))
        print(exchange)
        if(exchange[0] == "XAMS"):
            ticker = ticker + ".AS"
        if(exchange[0] == "XBRU"):
            ticker = ticker + ".BR"
        
        if allreadyExist == None:
            dividends = yf.Ticker(ticker).dividends
            dividends.index = dividends.index.tz_localize(None)
            today = datetime.today()
            start_date = datetime(today.year - 1, 1, 1)
            end_date = datetime(today.year, 1, 1) - timedelta(days=1)

            filtered_dividends = dividends[(dividends.index >= start_date) & (dividends.index <= end_date)]
            average_dividend = filtered_dividends.mean()
            dividend_months = pd.to_datetime(filtered_dividends.index).month.tolist()

            incremented_months = [(month % 12) + 1 for month in dividend_months]  
            for month in incremented_months:
                # Convert to full month name for expectedMonth
                month_name = datetime(today.year, month, 1).strftime('%B')
                
                # Assume expectedDay is the 15th of the next month
                expected_day_obj = datetime(today.year, month, 15)
                expected_day_str = expected_day_obj.strftime('%Y-%m-%d')

                query = """
                    INSERT INTO dividendExpectations 
                    (stockID, expectedMonth, expectedDividendPerShare, expectedDay) 
                    VALUES (?, ?, ?, ?)
                """
                inputs = [int(stock_id_result[0]), month_name, float(average_dividend), expected_day_str]
                securityFilters = [r'^\d+$',  r'^[A-Za-z]{1,10}$', r'^\d+\.\d+$', r'^\d{4}-\d{2}-\d{2}$']
                insert_data(query, inputs, securityFilters)

# An important assumption of this function is that a reasonable amount of tickers is allready in the local database
# If this is not the case, please download a pre-configured database and only then run this update
# The reason for this limitation, is the fair-use policy of yahoo finance, you can't query the site 2000 times in a second
    
def import_and_update_tickers(exchange):
    result = []
    if exchange == 'ALL':
        result = import_nyse_tickers()
        result.extend(import_euronext_tickers())
    if exchange == 'NYSE':
        result = import_nyse_tickers()    
    if exchange in ['XBRU', 'XAMS']:
        result = import_euronext_tickers()
    return(result)

# Some stocks have double listings, group registrations. However, they don't seem generally available.
# Solution for now is to only accept stocks, that can be bought, e.g. have a currentPrice
def is_ticker_available(ticker):
    # Many tickers have suffixes like PRG, PRF, etc. They descripe stocks with voting rights, backruptcy priorities, etc.
    # As my audiance is the common stockholder, i'm going to ignore those.
    if ' ' in ticker:
        return False
    else:
        try:
            # Try to fetch data for the ticker
            data = yf.Ticker(ticker).info['currentPrice']
            return True
        except Exception as e:
            # If an exception occurs, the ticker is not available
            return False


# Ticker specific functions

def import_euronext_tickers():
    messages = []

    # Define the current date for the URL
    current_date = datetime.now().strftime("%d/%m/%Y")
    date_added = datetime.now().strftime('%Y-%m-%d')
    url = Config.EURONEXTTickerURL + str(current_date)
          
    # Define exchange mapping
    # Edge case, sometimes a stock is on both AMX as Brussels: Euronext Amsterdam, Brussels, in thise case, it will default to XAMS
    exchange_mapping = {
        "Euronext Amsterdam": "XAMS",
        "Euronext Amsterdam, Brussels": "XAMS",
        "Euronext Brussels": "XBRU",
    }
    
    # Fetch the data
    response = requests.get(url)
    response.raise_for_status()  # Raise an error if the request failed
    data_lines = response.text.splitlines()  # Split the response into lines

    # Process each line
    for line in data_lines:
        # Remove quotes and split by delimiter (;)
        data = line.strip().replace('"', '').split(';')
        
        # Ensure the line has enough data fields
        if len(data) < 4:
            continue
        
        # Extract relevant fields
        stock_name = data[0]
        ticker = data[2]
        exchange_full = data[3]

        

        exchange = exchange_mapping.get(exchange_full)  # Map exchange name to XAMS/XBRU

        # Skip lines for exchanges other than XAMS or XBRU
        if not exchange:
            continue

        # Check if this ticker is already in the database (avoid duplicates)
        query = "SELECT COUNT(*) FROM Stocks WHERE ticker = ? AND Exchange = ?"
        myInputs = [ticker,exchange]
        securityFilters = [r'^[A-Za-z0-9]{1,20}$',r'^[A-Za-z0-9]{1,5}$']
        
        duplicateCheck = two_dynamic_query_STRING_one(query, myInputs,securityFilters)[0]
        if duplicateCheck > 0:
            continue

        if(exchange == "XAMS"):
            tmp_ticker = ticker + ".AS"
        if(exchange == "XBRU"):
            tmp_ticker = ticker + ".BR"
        
        if is_ticker_available(tmp_ticker):
            #Insert the data into the SQLite table
            query = "INSERT INTO Stocks (ticker, stockname, Exchange, DateAdded, Status, assetType) VALUES (?, ?, ?, ?, ?,?)"
            inputs = [ticker, stock_name, exchange, date_added, 'active', 'stock']
            securityFilters = [r'^[A-Za-z0-9]{1,20}$', r'^[A-Za-z0-9\s\.,;\$\%\+\-\=!&/\\]*$|^None$', r'^[A-Za-z0-9\s\.,;\$\%\+\-\=!&/\\]*$|^None$', r'^\d{4}-\d{2}-\d{2}$|^$|^None$', r'^[a-z]*$|^None$', r'^[A-Za-z]+$']
            insert_data(query, inputs, securityFilters)    
            tmp_message = "New ticker added: " + str(ticker)
            messages.append(tmp_message)

    return messages
    


# Ticker specific functions
    
def import_nyse_tickers():
    messages = []
    #is_ticker_available(ticker):
    response = requests.get(Config.NYSETickerURL)

    if response.status_code == 200:
        print("File downloaded successfully.")
    else:
       messages.append("Failed to download file from NYSE.")       

    content = response.text
    df = pd.read_csv(StringIO(content), sep="\t")
    df.columns = df.columns.str.strip()
    
    if 'Company' in df.columns and 'Symbol' in df.columns:
        filtered_df = df[(df['Auction'] == 'Y') & (df['Tape'] == 'Tape A')]
        filtered_df = filtered_df[['Company', 'Symbol']]
        filtered_df.rename(columns={'Company': 'stockname', 'Symbol': 'ticker'}, inplace=True)
        filtered_df['Exchange'] = 'XNYS'  
        filtered_df['DateAdded'] = datetime.now().strftime('%Y-%m-%d')
        filtered_df['Status'] = 'active'   
    
    query = "SELECT ticker FROM Stocks where exchange = 'XNYS'"
    db_tickers = simple_query(query)
    tickers = set([ticker[0] for ticker in db_tickers])
    
    for _, row in filtered_df.iterrows():
        if row['ticker'] not in tickers:
            if is_ticker_available(row['ticker']):
                tmp_msg = "New Ticker: " + str(row['ticker'])
                messages.append(tmp_msg)
                query = "INSERT INTO Stocks (ticker, stockname, Exchange, DateAdded, Status, assetType)VALUES (?, ?, ?, ?, ?, ?)"
                inputs = [row['ticker'], row['stockname'], row['Exchange'], row['DateAdded'], row['Status'], 'stock']
                securityFilters = [r'^[A-Za-z0-9]{1,20}$', r'^[A-Za-z0-9\s\.,;\$\%\+\-\=!&/\\]*$|^None$', r'^[A-Za-z0-9\s\.,;\$\%\+\-\=!&/\\]*$|^None$', r'^\d{4}-\d{2}-\d{2}$|^$|^None$', r'^[a-z]*$|^None$',r'^[A-Za-z]+$']
                insert_data(query, inputs, securityFilters)
            else:
                tmp_msg = "Not adding: " + str(row['ticker'])
                messages.append(tmp_msg)   
    return messages
    

