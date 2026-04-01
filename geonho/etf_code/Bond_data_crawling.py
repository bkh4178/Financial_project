#%%
'''
미국 국채 금리 (FRED)
	•	US10Y → DGS10
	•	US30Y → DGS30
'''
import pandas as pd
import pandas_datareader.data as web
import datetime

start = '2019-01-01'
end = '2025-12-31'

us10y = web.DataReader('DGS10', 'fred', start, end)
us30y = web.DataReader('DGS30', 'fred', start, end)

df_us = pd.concat([us10y, us30y], axis=1)
df_us.columns = ['US10Y', 'US30Y']
df_us.index.name = "date"

print(df_us.head())

#%%
'''
한국 국채 금리 (ECOS), API key 이용 수집
'''
from dotenv import load_dotenv
import os
import requests
import pandas as pd

load_dotenv()

api_key = os.getenv("ECOS_API_KEY")

def get_ecos(series_code, col_name):

    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{api_key}/json/kr/1/1000/817Y002/D/20190101/20251231/{series_code}"

    res = requests.get(url).json()

    if "StatisticSearch" not in res:
        print("ECOS ERROR:", res)
        return None

    data = res["StatisticSearch"]["row"]

    df = pd.DataFrame(data)

    df = df[["TIME","DATA_VALUE"]]
    df.columns = ["date", col_name]

    df["date"] = pd.to_datetime(df["date"])
    df[col_name] = df[col_name].astype(float)

    return df


kr3y = get_ecos("010200000","KR3Y")
kr10y = get_ecos("010400000","KR10Y")

df_kr = pd.merge(kr3y, kr10y, on="date")
df_kr = df_kr.set_index("date")

print(df_kr.head())

#%%
'''
yfinance -> ETF수집
'''
import yfinance as yf

tickers = [
    "TLT",
    "SHY",
    "148070.KS",  # KODEX 국고채3년
    "152380.KS"   # KODEX 국고채10년
]

data = yf.download(
    tickers,
    start="2019-01-01",
    end="2025-12-31"
)

prices = data["Close"]
prices.index.name = "date"

print(prices.head())

#%%
df_all = pd.concat([df_us, df_kr, prices], axis=1)
df_all = df_all.sort_index()
df_all = df_all.ffill()
df_all = df_all.dropna()
df_all.rename(columns={
    "148070.KS": "KODEX3Y",
    "152380.KS": "KODEX10Y"
}, inplace=True)

df_all.head(10)

#%%
df_all.to_csv("bond_dataset.csv")