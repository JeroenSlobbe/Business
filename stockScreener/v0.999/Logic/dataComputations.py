from datetime import date
from datetime import datetime
import cbsodata
from ecbdata import ecbdata
import yfinance as yf
import numpy as np
import requests
import pandas as pd
from io import StringIO
from Logic.database import *

def apply_3_sigma_filter(values):
    if not values:
        return []
    mean = np.mean(values)
    std_dev = np.std(values)
    return [x for x in values if mean - 3 * std_dev <= x <= mean + 3 * std_dev]

def fetch_and_store_benchmark_data():
    query = ("""
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
    """)
    latest_stock_data = simple_query(query)

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
    query = "SELECT id, yahooname FROM industries"
    industryList = simple_query(query)
    for industry_id, yahooname in industryList:
        industry_yahoo_names[industry_id] = yahooname

    # Step 5: Compute benchmarks for each industry
    benchmarks = []
    for industryID, metrics in industry_data.items():
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
    query = """
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
        """
    
    for benchmark in benchmarks:
        if (benchmark[-1] is not None) and (benchmark[-1] != "NULL"):
            securityFilters = [r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$', r'^-?\d+(\.\d+)?$|^$|^None$']
            insert_data(query, list(benchmark), securityFilters)
        else:
            print(benchmark)



