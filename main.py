import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os



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
    st.title("Efficient Frontier Optimiser")
    st.write('Select stock ticker and their weights to analyze the efficient frontier of your portfolio.')

    symbols = ['AAPL', 'ETH', 'ADA']  # Example symbols, you can modify this based on your API data

    start_date = st.date_input('Start Date', datetime.date(2021, 1, 1))
    end_date = st.date_input('End Date', datetime.date.today())

    data = {}
    for symbol in symbols:
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
    df.columns = symbols

    n_portfolios = st.slider('Choose number of randomly generated portfolios.', 20, 500, value=200)

    if st.button("Analyse"):
        selected_coins = symbols
        coin_percentages = [1.0 / len(selected_coins)] * len(selected_coins)

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
