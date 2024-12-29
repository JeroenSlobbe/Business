from flask import Flask, render_template, request, redirect, url_for
from Logic.logic import *
from Logic.data import *
from Config.profileConfiguration import *
import os
import subprocess
import threading
import requests

app = Flask(__name__)
dbLocation = 'stockDB.db'


@app.route("/")
def home():
    return render_template("home.html")  # Render a template for the home page

# Stock stuff
  
@app.route('/portfolio/view-portfolio', methods=['GET', 'POST'])
def view_portfolio():
    if request.method == 'POST':
        # Handle deletion of a transaction
        transaction_id = request.form.get('transaction_id')
        if transaction_id:
            delete_transaction(transaction_id)
        return redirect(url_for('view_portfolio'))

    # Fetch data
    portfolio_data = get_portfolio_data()
    transactions = get_all_transactions()
    dividend_expectations = calculate_dividend_expectations()
    
    # Calculations for summary boxes
    total_invested = sum(stock['invested'] for stock in portfolio_data)
    portfolio_value = sum(stock['current_value'] for stock in portfolio_data)
    total_dividends = sum(stock['dividends'] for stock in portfolio_data)
    total_return = ((portfolio_value + total_dividends - total_invested) / total_invested) * 100 if total_invested > 0 else 0
    total_exp_dividends = 0    
    for row in dividend_expectations:
        total_exp_dividends = total_exp_dividends + dividend_expectations[row]
    
    avg_monthly_dividends = total_exp_dividends / 12
    annual_dividends = total_exp_dividends
    
     
    
    return render_template('portfolio/portfolio_view.html', portfolio=portfolio_data,total_invested=total_invested,portfolio_value=portfolio_value,total_dividends=total_dividends, total_return=total_return,avg_monthly_dividends=avg_monthly_dividends, annual_dividends=annual_dividends, dividend_expectations=dividend_expectations,transactions=transactions)
    

@app.route('/portfolio/transactions', methods=['GET', 'POST'])
def transactions():
    if request.method == 'POST':
        # Handle deletion of a transaction
        transaction_id = request.form.get('transaction_id')
        if transaction_id:
            delete_transaction(transaction_id)
        return redirect(url_for('transactions'))

    # Fetch portfolio data and transactions
    portfolio_data = get_portfolio_data()
    transactions = get_all_transactions()

    return render_template('portfolio/transactions.html', portfolio=portfolio_data, transactions=transactions)


@app.route('/portfolio/fire', methods=['GET', 'POST'])
def fire_view():
    # Handle form submission for dividend record insertion or deletion
    if request.method == 'POST':
        if 'dividend_id' in request.form:  # Deleting a dividend
            dividend_id = request.form['dividend_id']
            delete_dividend(dividend_id)  # Call the delete function
        elif 'expectation_id' in request.form:  # Deleting a dividend expectation
            expectation_id = request.form['expectation_id']
            delete_dividend_expectation(expectation_id)  # Call the delete function
        else:  # Insert a new dividend
            insert_dividend(request)  # Call the insert function

        return redirect(url_for('fire_view'))

    # Fetch all recorded dividends and dividend expectations
    fire = get_dividents(dbLocation)  # Assuming this function returns dividend records
    expectations = get_dividend_expectations(dbLocation)  # Fetch dividend expectations
    stocks = list_stocks()  # Assuming this returns a list of stocks

    return render_template('portfolio/fire.html', fire=fire, stocks=stocks, expectations=expectations)

    
# Market & stock selection stuff

@app.route('/stock-seeker/view-industries')
def view_industries():
    industries_data = list_industries(dbLocation)
    return render_template('stock-seeker/view_industries.html', industries=industries_data)

@app.route('/stock-seeker/search-profile')
def search_profile():
    profiles = get_all_profiles()  # Fetch all profiles
    return render_template('stock-seeker/search_profile.html', profiles=profiles)


@app.route('/stock-seeker/evaluate-stock', defaults={'ticker': None})
@app.route('/stock-seeker/evaluate-stock/<string:ticker>')
def evaluate_stock(ticker):
    # Get the latest economic data
    economic_data = smoothenEconomicData(get_latest_economic_data(dbLocation))
    profile = get_profile(1)
    # If ticker is provided, fetch stock data
    if ticker:
        stock_data = get_stock_data(ticker)  # Get the stock data using the ticker
        if stock_data:  # If stock data is available, get the industry benchmark
            industry_id = stock_data["industryID"]
            benchmark_data = get_industry_benchmark_data(industry_id, dbLocation)
            verdicts = generateVerdicts(stock_data, profile)
        else:
            benchmark_data = {}  # If stock data is not found, set benchmark data as empty
    else:
        stock_data = None
        benchmark_data = {}
        verdicts = {}
    return render_template('stock-seeker/evaluate_stock.html', ticker=ticker,economic_data=economic_data, stock_data=stock_data, benchmark_data=benchmark_data, profile=profile, verdicts=verdicts)  # Pass the benchmark data


# Manage data

@app.route('/update-data/refresh-economic-data', methods=['GET'])
def refresh_economic():
    return render_template('update-data/refresh_economic.html')

@app.route('/update-data/refresh-stock')
def refresh_stock():
    return render_template('update-data/refresh_stock.html')

@app.route('/update-data/refresh-industry-benchmark')
def refresh_industry_benchmark():
    return render_template('update-data/refresh_industry_benchmark.html')



# Everything AJAX 

@app.route('/update-data/refresh-economic-data', methods=['POST'])
def refresh_economic_data():
    fetch_and_store_economic_data()
    return jsonify({"message": "Economic data refreshed successfully!"})

@app.route('/update-data/refresh-benchmark-data', methods=['POST'])
def refresh_benchmark_data():
    fetch_and_store_benchmark_data()
    return jsonify({"message": "Benchmark data refreshed successfully!"})

@app.route('/industries', methods=['GET'])
def get_industries():
    industries = list_industries()  # Directly calling the function as it's now imported
    return jsonify(industries)

@app.route('/get_stocks_by_industry_route/<int:industry_id>')
def get_stocks_by_industry_route(industry_id):
    # Call the function to get stocks based on the industry ID
    stocks = get_stock_by_industry(industry_id)
    return jsonify(stocks)


@app.route('/stock-seeker/load-stocks/<int:profileID>/<easeFactor>', methods=['GET'])
def load_stocks(profileID, easeFactor):
    profiles = get_all_profiles()  # Fetch all profiles
    profile = profiles[1]  # Get the specific profile by ID
    easeFactor = float(easeFactor)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404  # Handle the case if profile is not found
    
    # Fetch the stocks from the database as done before
    stocks = generate_watchlist(profile, easeFactor, dbLocation)

    # Format the response
    stock_data = [{"ticker": stock["ticker"], "stockname": stock["stockname"], "industry": stock["industry"]} for stock in stocks]
    
    return jsonify({"stocks": stock_data})



# Inserting information in the database
@app.route('/portfolio/add-transaction', methods=['POST'])
def add_transaction():
    insert_transaction(request,dbLocation)
    return redirect('transactions')


@app.route('/portfolio/set-dividend-expectations', methods=['POST'])
def set_dividend_expectations():
    insert_dividend_expectation(request)
    return redirect(url_for('fire_view'))

## Fixing ajax

@app.route('/start-update', methods=['GET', 'POST'])
def start_update():
    print("Main application trying to do something")
    try:
        response = requests.post('http://127.0.0.1:5001/start-update')
        if response.status_code == 202:
            return jsonify({}), 202, {'Location': 'http://127.0.0.1:5001/status'}
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        print("Error: ", e)
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def task_status():
    try:
        response = requests.get('http://127.0.0.1:5001/status')
        return jsonify(response.json())
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/errors')
def get_errors():
    try:
        response = requests.get('http://127.0.0.1:5001/errors')
        return jsonify(response.json())
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
