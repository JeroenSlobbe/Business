import sqlite3
from datetime import date
import cbsodata
from ecbdata import ecbdata
import yfinance as yf
import numpy as np

dbLocation = 'stockDB.db'  # Ensure this is the correct path to your database

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
    dataFiltered = [x for x in data if x['SoortMutaties'] == 'Volume, t.o.v. zelfde periode vorig jaar']
    return dataFiltered[-1]['BbpGecorrigeerdVoorWerkdageneffecten_3']

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

    conn = sqlite3.connect(dbLocation)
    cursor = conn.cursor()
    insert_query = """
    INSERT INTO economyhistory (date, inflation, ECBInterest, NL_Unemployment, NL_ConsumerConfidence, EUR_USD_ExchangeRate, NL_GDPGrowth, NL_RetailSales, NL_IndustrialProduction, NL_Bankrupcies)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(insert_query, (timestamp, inflation, ECBIR, unemployment, consumerConfidence, EUR_USD_ExchangeRate, GDPGrowth, NL_RetailSales, NL_IndustrialProduction, NL_Bankrupcies))
    conn.commit()
    conn.close()

def fetch_and_store_benchmark_data():
    conn = sqlite3.connect(dbLocation)
    cursor = conn.cursor()
    # List of stock IDs to exclude
    excluded_stock_ids = [2663]

    # Prepare the SQL query with the exclusion condition
    cursor.execute("""
        SELECT 
            sh.stockID, sh.date, sh.price, sh.operatingIncom, sh.icr, sh.currentRatio,
            sh.pbratio, sh.peratio, sh.beta, sh.lastReturn, sh.fiveYearAverageReturn,
            sh.dividentYield, sh.RandDExpense, sh.revenue, 
            sh.percentageMakingProfitLastFiveYears, s.industryID
        FROM stockhistory sh
        JOIN (
            SELECT stockID, MAX(date) AS latest_date
            FROM stockhistory
            GROUP BY stockID
        ) latest ON sh.stockID = latest.stockID AND sh.date = latest.latest_date
        JOIN Stocks s ON sh.stockID = s.id
        WHERE sh.stockID NOT IN ({})
    """.format(','.join('?' * len(excluded_stock_ids))), tuple(excluded_stock_ids))
    latest_stock_data = cursor.fetchall()

    # Step 3: Organize data by industry for aggregation
    industry_data = {}
    for row in latest_stock_data:
        stockID, date, price, operatingIncome, icr, currentRatio, pbratio, peratio, beta, \
        lastReturn, fiveYearAvgReturn, dividendYield, randDExpense, revenue, profitPct, industryID = row

        # Only process non-zero values
        if industryID not in industry_data:
            industry_data[industryID] = {
                "price": [],
                "operatingIncome": [],
                "icr": [],
                "currentRatio": [],
                "pbratio": [],
                "peratio": [],
                "beta": [],
                "lastReturn": [],
                "fiveYearAvgReturn": [],
                "dividendYield": [],
                "randDPercentage": [],
                "profitPercentage": [],
            }

        # Append values for aggregation if they are not zero
        if price: industry_data[industryID]["price"].append(price)
        if beta: industry_data[industryID]["beta"].append(beta)
        if peratio: industry_data[industryID]["peratio"].append(peratio)
        if pbratio: industry_data[industryID]["pbratio"].append(pbratio)
        if icr: industry_data[industryID]["icr"].append(icr)
        if currentRatio: industry_data[industryID]["currentRatio"].append(currentRatio)
        if dividendYield: industry_data[industryID]["dividendYield"].append(dividendYield)
        if randDExpense and revenue: 
            industry_data[industryID]["randDPercentage"].append(randDExpense * 100 / revenue)
        if lastReturn: industry_data[industryID]["lastReturn"].append(lastReturn)
        if fiveYearAvgReturn: industry_data[industryID]["fiveYearAvgReturn"].append(fiveYearAvgReturn)
        if profitPct: industry_data[industryID]["profitPercentage"].append(profitPct)

    # Step 4: Fetch the yahooname for each industry
    industry_yahoo_names = {}
    cursor.execute("SELECT id, yahooname FROM industries")
    for industry_id, yahooname in cursor.fetchall():
        industry_yahoo_names[industry_id] = yahooname

    # Step 5: Compute benchmarks for each industry
    benchmarks = []
    for industryID, metrics in industry_data.items():
        def apply_3_sigma_filter(values):
            if not values:
                return []
            mean = np.mean(values)
            std_dev = np.std(values)
            return [x for x in values if mean - 3 * std_dev <= x <= mean + 3 * std_dev]

        # Apply the 3-sigma filter to each metric
        for key in metrics:
            metrics[key] = apply_3_sigma_filter(metrics[key])

        # Compute averages for filtered data
        avg_price = np.mean(metrics["price"]) if metrics["price"] else None
        avg_beta = np.mean(metrics["beta"]) if metrics["beta"] else None
        avg_peratio = np.mean(metrics["peratio"]) if metrics["peratio"] else None
        avg_pbratio = np.mean(metrics["pbratio"]) if metrics["pbratio"] else None
        avg_icr = np.mean(metrics["icr"]) if metrics["icr"] else None
        avg_current_ratio = np.mean(metrics["currentRatio"]) if metrics["currentRatio"] else None
        avg_div_yield = np.mean(metrics["dividendYield"]) if metrics["dividendYield"] else None
        avg_rand_d = np.mean(metrics["randDPercentage"]) if metrics["randDPercentage"] else None
        avg_last_return = np.mean(metrics["lastReturn"]) if metrics["lastReturn"] else None
        avg_five_year_return = np.mean(metrics["fiveYearAvgReturn"]) if metrics["fiveYearAvgReturn"] else None
        avg_profit_pct = np.mean(metrics["profitPercentage"]) if metrics["profitPercentage"] else None

        yahooname = industry_yahoo_names.get(industryID, "Unknown")
        benchmarks.append((
            avg_price, avg_beta, avg_peratio, avg_pbratio, avg_icr, 
            avg_current_ratio, avg_div_yield, avg_rand_d, avg_last_return, 
            avg_five_year_return, avg_profit_pct, industryID
        ))

    # Step 6: Perform Update or Insert (Upsert) for each industry
    for benchmark in benchmarks:
        cursor.execute("""
            INSERT INTO industryBenchmark (price, beta, peratio, pbratio, icr, currentRatio, 
                                           dividentYield, percRandD, lastReturn, fiveYearAverageReturn, 
                                           percentageMakingProfitLastFiveYears, industryID)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(industryID) DO UPDATE SET
                price=excluded.price, beta=excluded.beta, peratio=excluded.peratio, pbratio=excluded.pbratio,
                icr=excluded.icr, currentRatio=excluded.currentRatio, dividentYield=excluded.dividentYield,
                percRandD=excluded.percRandD, lastReturn=excluded.lastReturn,
                fiveYearAverageReturn=excluded.fiveYearAverageReturn,
                percentageMakingProfitLastFiveYears=excluded.percentageMakingProfitLastFiveYears
        """, benchmark)

    conn.commit()
    conn.close()