import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import time
import datetime
import plotly.graph_objects as go
import plotly.express as px
import requests

def get_data(symbol, start_date, end_date):
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol='+symbol+'&outputsize=full&apikey=IAGDKXNPPS0NVXYR'
    r = requests.get(url)
    data = r.json()
    time_series = data['Time Series (Daily)']
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())
    filtered_data = {date: values for date, values in time_series.items() 
                     if start_timestamp <= datetime.datetime.strptime(date, '%Y-%m-%d').timestamp() <= end_timestamp}
    return filtered_data

def fetch_candlestick_data(ticker):
    end_date = int(time.time())
    start_date = int(time.mktime((datetime.datetime.now() - datetime.timedelta(days=365)).timetuple()))
    data = get_data(ticker, start_date, end_date)
    return data

# fetch_candlestick_data("AAPL")
def create_line_chart(symbols):
    end_date = int(time.time())
    start_date = int(time.mktime((datetime.datetime.now() - datetime.timedelta(days=365)).timetuple()))
    
    fig = go.Figure()
    colors = px.colors.qualitative.Plotly  # Get the qualitative color palette from Plotly Express
    for i, symbol in enumerate(symbols):
        data = get_data(symbol, start_date, end_date)
        if data:
            dates = [datetime.datetime.strptime(date, '%Y-%m-%d') for date in data.keys()]
            prices = [float(data[date]['4. close']) for date in data.keys()]
            fig.add_trace(go.Scatter(x=dates, y=prices, mode='lines', name=symbol, line=dict(color=colors[i % len(colors)])))

    fig.update_layout(title="Stock Prices",
                      xaxis_title="Date",
                      yaxis_title="Price ($)",
                      xaxis_rangeslider_visible=False)

    return fig
    
def efficient_frontier(df, n_portfolios=100):
    # Calculate the covariance matrix for the portfolio.
    portfolio_covariance = df.cov()

    # Lists to store weights, returns and risk values.
    portfolio_returns = []
    portfolio_stds = []
    coin_weights = []
    pair = []

    coin_names = df.columns
    coin_means = df.mean().to_numpy()

    # Generate data, giving each coin a random weight.
    while len(portfolio_stds) < n_portfolios:
        # Initial values.
        check = False
        portfolio_return = 0

        # Make a portfolio with random weights for each coin.
        coin_weight = np.random.random(len(coin_names))
        # Normalise to 1.
        coin_weight /= np.sum(coin_weight)

        # Calculate the expected return value of the random portfolio.
        for i in range(len(coin_names)):
            portfolio_return += coin_weight[i] * coin_means[i]
        #---Calculate variance, use it for the deviation.
        portfolio_variance = np.dot(np.dot(coin_weight.transpose(), portfolio_covariance), coin_weight)
        portfolio_std = np.sqrt(portfolio_variance)

        pair.append([portfolio_return, portfolio_std])
        for R,V in pair:
            if (R > portfolio_return) and (V < portfolio_std):
                check = True
                break
        if check:
            continue

        portfolio_stds.append(portfolio_std)
        portfolio_returns.append(portfolio_return)
        coin_weights.append([i * 100 for i in coin_weight])

    ef_df = pd.DataFrame(coin_weights)
    ef_df.columns = coin_names
    ef_df.insert(0, "Return", portfolio_returns, True)
    ef_df.insert(1, "Risk", portfolio_stds, True)
    return ef_df, portfolio_stds, portfolio_returns

def users_point(df, coin_weight):
    # Calculate the covariance matrix for the portfolio.
    portfolio_covariance = df.cov()
    coin_names = df.columns
    coin_means = df.mean().to_numpy()
    
    # Normalise to 1.
    coin_weight /= np.sum(coin_weight)
    
    portfolio_return = 0
    
    # Calculate the expected return value of the random portfolio.
    for i in range(0, len(coin_names)):
        portfolio_return += coin_weight[i] * coin_means[i]
    #---Calculate variance, use it for the deviation.
    portfolio_variance = np.dot(np.dot(coin_weight.transpose(), portfolio_covariance), coin_weight)
    portfolio_std = np.sqrt(portfolio_variance)

    return portfolio_std, portfolio_return

def main():
    st.title('Nasdaq Portfolio Analysis')
    st.write('Select tickers and their weights to analyze the efficient frontier of your portfolio.')

    nasdaq_tickers = pd.read_csv("nasdaq-listed.csv")['Symbol']

    selected_coins = st.multiselect(label="Select tickers: ", options=nasdaq_tickers)

    buttons = {}
    if selected_coins != []:
        st.markdown("Enter the percentage each tickers contributes to your portfolio's total value.")
        for coin_code in selected_coins:
            buttons[coin_code] = st.number_input(coin_code, 0, 100, key=coin_code)

        n_portfolios = st.slider('Choose number of randomly generated portfolios.', 20, 500, value=200)

        if st.button("Analyse"):
            if len(selected_coins) < 2:
                st.warning("You must enter at least two tickers")
            elif sum(buttons.values()) != 100:
                st.warning("Portfolio total is not 100%.")
            else:
                coin_percentages = [buttons.get(coin, 0) for coin in selected_coins]

                end_date = datetime.datetime.now().date()
                start_date = end_date - datetime.timedelta(days=365)

                data = {}
                for symbol in selected_coins:
                    data[symbol] = get_data(symbol, start_date, end_date)

                df = pd.DataFrame.from_dict({(i, j): data[i][j] 
                                              for i in data.keys() 
                                              for j in data[i].keys()},
                                             orient='index')

                # Assuming '4. close' is the column containing closing prices
                df['4. close'] = pd.to_numeric(df['4. close'], errors='coerce')

                # Reshape DataFrame
                df.reset_index(inplace=True)
                df['index'] = pd.to_datetime(df['index'])
                df.set_index('index', inplace=True)
                df.columns = selected_coins

                ef_df, portfolio_stds, portfolio_returns = efficient_frontier(df[selected_coins], n_portfolios)

                fig = go.Figure()
                for i, row in ef_df.iterrows():
                    fig.add_trace(go.Scatter(x=[row['Risk']], y=[row['Return']], mode='markers', marker=dict(color='blue')))

                users_risk, users_return = users_point(df[selected_coins], coin_percentages)
                fig.add_trace(go.Scatter(x=[users_risk], y=[users_return], mode='markers', marker=dict(color='green'), name='Your Portfolio'))

                df_optimal_return = find_optimal_return(ef_df, users_risk)
                fig.add_trace(go.Scatter(x=[df_optimal_return['Risk']], y=[df_optimal_return['Return']], mode='markers', marker=dict(color='red'), name='Optimal Return (same risk)'))

                df_optimal_risk = find_optimal_risk(ef_df, users_return)
                fig.add_trace(go.Scatter(x=[df_optimal_risk['Risk']], y=[df_optimal_risk['Return']], mode='markers', marker=dict(color='orange'), name='Optimal Risk (same return)'))

                fig.update_layout(title="Efficient Frontier Analysis",
                                  xaxis_title="Risk (%)",
                                  yaxis_title="Return (%)",
                                  legend=dict(x=0, y=1, traceorder='normal'))

                st.plotly_chart(fig)                     
                st.markdown(f"**Your portfolio risk is **{users_risk:.1f}%")
                st.markdown(f"**Your expected daily returns are **{users_return:.2f}%")
        
                st.header("Maximum returns portfolio (same risk)")
                st.markdown("Maximising your expected returns, whilst keeping the risk the same, your portfolio should look like:") 
                st.dataframe(df_optimal_return.round(2))
                
                st.header("Minimum risk portfolio (same returns)")
                st.markdown("Minimising your risk, whilst keeping the returns the same, your portfolio should look like:")
                st.dataframe(df_optimal_risk.round(2))

if __name__ == "__main__":
    main()
