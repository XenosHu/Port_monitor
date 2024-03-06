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
import csv

def get_data(symbol, start_date, end_date):
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol='+symbol+'&outputsize=full&apikey=IAGDKXNPPS0NVXYR'
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol='+symbol+'&outputsize=full&apikey=D43BNKTSJQMGD8GN'
    r = requests.get(url)
    data = r.json()
    
    time_series = data['Time Series (Daily)']
    filtered_data = [(date, values['1. open'], values['2. high'], values['3. low'], values['4. close'], values['5. volume'])
                     for date, values in time_series.items() 
                     if start_date <= datetime.datetime.strptime(date, '%Y-%m-%d').date() <= end_date]
    df = pd.DataFrame(filtered_data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    filtered_data = df
    return filtered_data
    
import efficient_frontier
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

st.title('Nasdaq Portfolio Analysis')
st.write('Select tickers and their weights to analyze the efficient frontier of your portfolio.')
nasdaq_tickers = pd.read_csv("nasdaq-listed.csv")['Symbol']
selected_coins = st.multiselect(label="Select tickers: ", options=nasdaq_tickers)

buttons = {}

if selected_coins != []:
    st.markdown("Enter the percentage each cryptocurrency contributes to your portfolio's total value.")

def total_percentage():
    return sum(list(buttons.values()))

for coin_code in selected_coins:
    buttons[coin_code] = st.number_input(coin_code, 0, 100, key=coin_code)

n_portfolios = st.slider('Choose number of randomly generated portfolios.', 20, 500, value=200)

if st.button("Analyse"):
    if selected_coins == [] or len(selected_coins) < 2:
        st.warning("You must enter at least two cryptocurrencies")
    elif total_percentage() != 100:
        st.warning("Portfolio total is not 100%.")
    else:
        selected_coins = list(buttons.keys())
        coin_percentages = list(buttons.values())

        df = pd.read_csv(data_path)[selected_coins]
        users_risk, users_return = efficient_frontier.users_point(df, coin_percentages)
        df, risk, returns = efficient_frontier.efficient_frontier(df, n_portfolios)

        fig, ax = plt.subplots()
        ax.scatter(risk, returns, label="Randomly generated portfolios")
        ax.scatter(users_risk, users_return, label="Your portfolio")
        ax.set_xlabel("Daily risk (%)")
        ax.set_ylabel("Daily returns (%)")

        df_optimal_return = efficient_frontier.find_optimal_return(df, users_risk)
        df_optimal_return.name = "(%)"
        ax.scatter(df_optimal_return["Risk"], df_optimal_return["Return"], label="Optimal returns (same risk)")

        df_optimal_risk = efficient_frontier.find_optimal_risk(df, users_return)
        df_optimal_risk.name = "(%)"
        ax.scatter(df_optimal_risk["Risk"], df_optimal_risk["Return"], label="Optimal risk (same returns)")

        ax.legend()
        st.pyplot(fig)

        st.markdown("**Your portfolio risk is **" + str("{:.1f}".format(users_risk)) + "%")
        st.markdown("**Your expected daily returns are **" + str("{:.2f}".format(users_return)) + "%")

        st.header("Maximum returns portfolio (same risk)")
        st.markdown("Maximising your expected returns, whilst keeping the risk the same, your portfolio should look like:") 
        st.dataframe(df_optimal_return.round(2))
        
        st.header("Minimum risk portfolio (same returns)")
        st.markdown("Minimising your risk, whilst keeping the returns the same, your portfolio should look like:")
        st.dataframe(df_optimal_risk.round(2))
        
