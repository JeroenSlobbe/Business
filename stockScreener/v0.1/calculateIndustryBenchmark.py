import sqlite3

def compute_industry_benchmarks(database_path):
    # Step 1: Connect to the SQLite database
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()


    # List of stock IDs to exclude, for example if a growth stock is listed in a conservative market, the R&D metric can become skewed. For these cases, this exlcude list should be used.
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
    print("\nIndustry Benchmark Overview:")
    print("-" * 80)
    for industryID, metrics in industry_data.items():
        # Compute averages, excluding industries with no data for specific metrics
        avg_price = sum(metrics["price"]) / len(metrics["price"]) if metrics["price"] else None
        avg_beta = sum(metrics["beta"]) / len(metrics["beta"]) if metrics["beta"] else None
        avg_peratio = sum(metrics["peratio"]) / len(metrics["peratio"]) if metrics["peratio"] else None
        avg_pbratio = sum(metrics["pbratio"]) / len(metrics["pbratio"]) if metrics["pbratio"] else None
        avg_icr = sum(metrics["icr"]) / len(metrics["icr"]) if metrics["icr"] else None
        avg_current_ratio = sum(metrics["currentRatio"]) / len(metrics["currentRatio"]) if metrics["currentRatio"] else None
        avg_div_yield = sum(metrics["dividendYield"]) / len(metrics["dividendYield"]) if metrics["dividendYield"] else None
        avg_rand_d = sum(metrics["randDPercentage"]) / len(metrics["randDPercentage"]) if metrics["randDPercentage"] else None
        avg_last_return = sum(metrics["lastReturn"]) / len(metrics["lastReturn"]) if metrics["lastReturn"] else None
        avg_five_year_return = sum(metrics["fiveYearAvgReturn"]) / len(metrics["fiveYearAvgReturn"]) if metrics["fiveYearAvgReturn"] else None
        avg_profit_pct = sum(metrics["profitPercentage"]) / len(metrics["profitPercentage"]) if metrics["profitPercentage"] else None

        # Fetch yahooname for the current industry
        yahooname = industry_yahoo_names.get(industryID, "Unknown")

        # Print benchmark data for the industry
        print(f"Industry ID {industryID} ({yahooname}):")
        print(f"  Avg Price: {avg_price}")
        print(f"  Avg Beta: {avg_beta}")
        print(f"  Avg PE Ratio: {avg_peratio}")
        print(f"  Avg PB Ratio: {avg_pbratio}")
        print(f"  Avg ICR: {avg_icr}")
        print(f"  Avg Current Ratio: {avg_current_ratio}")
        print(f"  Avg Dividend Yield: {avg_div_yield}")
        print(f"  Avg R&D Percentage: {avg_rand_d}")
        print(f"  Avg Last Return: {avg_last_return}")
        print(f"  Avg Five Year Return: {avg_five_year_return}")
        print(f"  Avg Profit Percentage: {avg_profit_pct}")
        print("-" * 80)

        # Prepare for upsert operation
        benchmarks.append((
            avg_price, avg_beta, avg_peratio, avg_pbratio, avg_icr, 
            avg_current_ratio, avg_div_yield, avg_rand_d, avg_last_return, 
            avg_five_year_return, avg_profit_pct, industryID
        ))

    # Step 6: Perform Update or Insert (Upsert) for each industry
    for benchmark in benchmarks:
        avg_price, avg_beta, avg_peratio, avg_pbratio, avg_icr, avg_current_ratio, avg_div_yield, \
        avg_rand_d, avg_last_return, avg_five_year_return, avg_profit_pct, industryID = benchmark
        
        # Check if the record exists for the given industryID
        cursor.execute("SELECT COUNT(1) FROM industryBenchmark WHERE industryID = ?", (industryID,))
        exists = cursor.fetchone()[0]

        if exists:
            # If the record exists, update it
            cursor.execute("""
                UPDATE industryBenchmark
                SET 
                    price = ?, beta = ?, peratio = ?, pbratio = ?, icr = ?, 
                    currentRatio = ?, dividentYield = ?, percRandD = ?, lastReturn = ?, 
                    fiveYearAverageReturn = ?, percentageMakingProfitLastFiveYears = ?
                WHERE industryID = ?
            """, benchmark)
        else:
            # If the record doesn't exist, insert a new record
            cursor.execute("""
                INSERT INTO industryBenchmark 
                (price, beta, peratio, pbratio, icr, currentRatio, dividentYield, 
                percRandD, lastReturn, fiveYearAverageReturn, percentageMakingProfitLastFiveYears, industryID)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, benchmark)

    # Commit and close the connection
    conn.commit()
    conn.close()

    print("\nBenchmark computation completed and inserted/updated in the database.")

# Call the function with the path to your database
compute_industry_benchmarks("ScreeningsDB.db")
