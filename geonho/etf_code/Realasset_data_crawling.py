#%%
import yfinance as yf
import pandas as pd

tickers = [
    "GC=F",  # Gold futures
    "SI=F",  # Silver futures
    "CL=F"   # WTI futures
]

data = yf.download(
    tickers,
    start="2019-01-01",
    end="2025-12-31"
)

df_spot = data["Close"]

df_spot.columns = [
    "GoldSpot",
    "SilverSpot",
    "WTI"
]

df_spot.index.name = "date"

print(df_spot.head())

#%%
'''
Commodity ETF Prices
'''

import yfinance as yf

tickers = [
    "GLD",
    "SLV",
    "USO"
]

data = yf.download(
    tickers,
    start="2019-01-01",
    end="2025-12-31"
)

df_etf = data["Close"]

df_etf.columns = [
    "GLD",
    "SLV",
    "USO"
]

df_etf.index.name = "date"

print(df_etf.head())

#%%
df_realasset = pd.concat([df_spot, df_etf], axis=1)

df_realasset = df_realasset.sort_index()
df_realasset = df_realasset.ffill()
df_realasset = df_realasset.dropna()

df_realasset.to_csv("realasset_dataset.csv")