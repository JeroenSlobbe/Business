= Engineering imrpovements
	[x] remove db from logic.py and create seperate database handler
	[x] add datalayer, so other sources can be more easily added
		[x] Improve securityFilter, error:
			[x] Security violation INSERT INTO stockhistory (stockID,date,price,operatingIncom, percentageMakingProfitLastFiveYears, icr, currentRatio,pbratio, peratio,beta,lastReturn,fiveYearAverageReturn,dividentYield,RandDExpense,currency, revenue)VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?); on:  5 out of:  [146, datetime.date(2025, 1, 24), 42.9, 1172000000.0, 80, nan, 45.214, 0.56, 10.12, 0.733, 23.11, 18.01, 10.42, 0, 'EUR', 10974000000.0]
			[x] Security violation INSERT INTO stockhistory (stockID,date,price,operatingIncom, percentageMakingProfitLastFiveYears, icr, currentRatio,pbratio, peratio,beta,lastReturn,fiveYearAverageReturn,dividentYield,RandDExpense,currency, revenue)VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?); on:  12 out of:  [272, datetime.date(2025, 2, 15), 0, 0, 0, 0, None, 0, 0, 0, -0.68, 0.64, inf, 0, 'USD', 0]
			[x] Security violation INSERT INTO stockhistory (stockID,date,price,operatingIncom, percentageMakingProfitLastFiveYears, icr, currentRatio,pbratio, peratio,beta,lastReturn,fiveYearAverageReturn,dividentYield,RandDExpense,currency, revenue)VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?); on:  12 out of:  [3174, datetime.date(2025, 2, 22), 75.58, 0, 0, 0, None, 0, 0, 0, 20.97, 11.51, 2.134257601779355e-05, 0, 'USD', 0]
	[x] fix bug (BWSN view)
	[x] Configuration file
	[x] add database index to remove performance issues when loading stocks by profile
	[x] update yfinance libary to get rid of the block
	[x] add token refresh for stock refresher each hour
	[x] fix dividend table padding
	[x] fix percentages
	[x] fix status = special/active
	[x] fix insert stock, assetType='stock' or 'bond'
	[x] See if multiple stock queries bypasses rate limit and if so implement major timing improvement
		-> explored option, but download only works for stock value, not the statistics I would like to analyse
	[x] fix that bonds are also updated (but regularMarketPrice as price only)
	[x] add token refresh for the error page (while fetching data)
	[x] GDP Growth bug
	[x] fix "ams and brussels" bug + input filter bug
	
= Security improvements
	[x] strickt input validation
	[x] fix enters and commas for strategic evaluation
	[x] header security
	[X] dataapp (JWT)

= Features (must have)
	[x] Make stock profile editable
	[x] Daily auto-refresh the stocks from portfolio
	[x] Improve CSS
	[x] Automate Dividend expectations
	[x] Add manual bond adder
	[x] generate portfolio statistics (Currency / geography exposure + asset type %)
	[x] add inpage update / value dividend expectation (and payout) updates
	[x] view purchase conditions
	[x] add support for ETFs
	

