import yfinance as yf
import pandas as pd

START_DATE = "2019-01-01"
END_DATE   = "2025-12-31"
OUTPUT     = "data/raw/etf_price/vix_daily.csv"

vix = yf.download("^VIX", start=START_DATE, end=END_DATE, progress=False)

vix.columns = [col[0] if isinstance(col, tuple) else col for col in vix.columns]
vix = vix[["Open", "High", "Low", "Close", "Volume"]].copy()
vix.index.name = "Date"
vix = vix.dropna(subset=["Close"]).sort_index()
vix = vix.reset_index()

vix.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

print(f"수집 완료: {len(vix)}일")
print(f"기간: {vix['Date'].min().date()} ~ {vix['Date'].max().date()}")
print(f"종가 범위: {vix['Close'].min():.2f} ~ {vix['Close'].max():.2f}")
print(f"저장: {OUTPUT}")
print(vix.head())
