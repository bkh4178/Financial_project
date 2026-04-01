#%%
'''
Dollar Index (FRED)
'''

import pandas_datareader.data as web
import pandas as pd

start = "2019-01-01"
end = "2025-12-31"

dxy = web.DataReader("DTWEXBGS", "fred", start, end)

dxy.columns = ["DXY"]
dxy.index.name = "date"

print(dxy.head())

#%%
#%%
'''
Dollar ETF
'''

import yfinance as yf

data = yf.download(
    "UUP",
    start="2019-01-01",
    end="2025-12-31"
)

uup = data["Close"]
uup.columns = ["UUP"]
uup.index.name = "date"

print(uup.head())

#%%
df_dollar = pd.concat([dxy, uup], axis=1)

df_dollar = df_dollar.sort_index()
df_dollar = df_dollar.ffill()
df_dollar = df_dollar.dropna()

df_dollar.to_csv("dollar_dataset.csv")