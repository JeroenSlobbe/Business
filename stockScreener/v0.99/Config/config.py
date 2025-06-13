# Application specific configuration
class Config:
    baseURL = 'http://127.0.0.1:5000'
    basePort = 5000
    dataURL = 'http://127.0.0.1:5001'
    dataPort = 5001
    debug = True
    dbLocation = 'stockDB.db'
    
    #Security (dataApp.py)
    JWT_SECRET_KEY = "PleaseChangeThisGITRepositoryPlaceHolder"
    JWT_ACCESS_TOKEN_EXPIRES = 7200 # Token expires in 2 hours (enough time to pull Euronext and NYSE from yahoofinance)
    
    #Security (app.py)
    DATA_APP_API_KEY = "PleaseChangeThisAPI_KEY_GITRepositoryPlaceHolder"
    LOGIN_URL = 'http://127.0.0.1:5001/token'
    PROTECTED_URL = 'http://127.0.0.1:5001/protected'
    
    # Data sources
    NYSETickerURL = 'https://www.nyse.com/publicdocs/nyse/markets/nyse/NYSE_and_NYSE_MKT_Trading_Units_Daily_File.xls'
    EURONEXTTickerURL = 'https://live.euronext.com/en/pd_es/data/stocks/download?mics=dm_all_stock&market=06%2C07&initialLetter=&fe_type=txt&fe_decimal_separator=&fe_date_format=d%2Fm%2FY&date='
   
    # Supported exchanges
    exchanges = ['NYSE', 'XAMS','XBRU']
    
    # Bond fixes
    bondIndustryID = 146
    bondSectorID = 12

    # ETF fixes
    etfIndustryID = 147
    etfSectorID = 13
    
    # Data fetching
    sleepTime = 120
    randomSleepLow = 0.2
    randomSleepHigh = 1.2
    