
import pandas as pd
import numpy as np
from pykrx import stock
import yfinance as yf
from datetime import datetime, timedelta
import warnings
import time
import os

warnings.filterwarnings('ignore')

# 1. 설정값

# 수집 기간: 5년치 (포트폴리오 최적화에 충분한 히스토리 확보)
START_DATE = "20190101"
END_DATE   = "20251231"


print(f"수집 기간: {START_DATE} ~ {END_DATE}")
print(f"(약 5년치 일별 데이터)\n")


# 2. 종목 리스트

# 원본 엑셀에서 구분2 기준으로 필터링
# 포함: 국내주식_지수, 해외주식_지수
# 제외: 국내주식_섹터, 해외주식_섹터, FX 및 원자재,
#       금리연계형/초단기채권, 해외채권_회사채, 해외채권_종합,
#       국내채권_회사채, 국내채권_종합

df_raw = pd.read_excel('/Users/jinwoong/Desktop/Bitamin/project/time-series_project_2/주식종목리스트.xlsx', sheet_name='ETF (187)', header=3)
df_raw.columns = ['drop', '티커', 'ETF명', 'AUM(억원)', '기초지수', '구분1', '구분2']
df_raw = df_raw.drop(columns=['drop']).dropna(subset=['티커'])
df_raw = df_raw[df_raw['티커'] != '티커']
df_raw['AUM(억원)'] = pd.to_numeric(df_raw['AUM(억원)'], errors='coerce')

INCLUDE_CATEGORIES = ['국내주식_지수', '해외주식_지수']
df_filtered = df_raw[df_raw['구분2'].isin(INCLUDE_CATEGORIES)].reset_index(drop=True)

print(f"필터링 후 총 종목 수: {len(df_filtered)}개")
print(f"  - 국내주식_지수: {len(df_filtered[df_filtered['구분2']=='국내주식_지수'])}개")
print(f"  - 해외주식_지수: {len(df_filtered[df_filtered['구분2']=='해외주식_지수'])}개\n")

# pykrx용 티커: A 제거 후 6자리 숫자
df_filtered['티커_krx'] = df_filtered['티커'].str.replace('A', '', regex=False)


# 3. 국내 ETF 데이터 수집 (pykrx)

print("=" * 50)
print("국내 ETF 데이터 수집 중 (pykrx)...")
print("=" * 50)

domestic = df_filtered[df_filtered['구분2'] == '국내주식_지수'].copy()
all_domestic = []

for _, row in domestic.iterrows():
    ticker = row['티커_krx']
    name   = row['ETF명']
    try:
        df_ohlcv = stock.get_market_ohlcv_by_date(START_DATE, END_DATE, ticker)
        if df_ohlcv.empty:
            print(f"  [SKIP] {name} ({ticker}) - 데이터 없음")
            continue

        df_ohlcv = df_ohlcv.reset_index()
        df_ohlcv.columns = df_ohlcv.columns.str.strip()

        # 날짜 컬럼 통일
        date_col = [c for c in df_ohlcv.columns if '날짜' in c or 'Date' in c or 'date' in c]
        if date_col:
            df_ohlcv = df_ohlcv.rename(columns={date_col[0]: 'Date'})
        else:
            df_ohlcv = df_ohlcv.rename(columns={df_ohlcv.columns[0]: 'Date'})

        df_ohlcv['티커']   = ticker
        df_ohlcv['ETF명']  = name
        df_ohlcv['구분']   = '국내주식_지수'
        df_ohlcv['통화']   = 'KRW'

        # 수익률 계산
        close_col = [c for c in df_ohlcv.columns if '종가' in c or 'Close' in c]
        if close_col:
            df_ohlcv['일별수익률'] = df_ohlcv[close_col[0]].pct_change()

        all_domestic.append(df_ohlcv)
        print(f"  [OK] {name} ({ticker}) - {len(df_ohlcv)}일")
        time.sleep(0.3)  # API 과부하 방지

    except Exception as e:
        print(f"  [ERR] {name} ({ticker}) - {e}")

df_domestic = pd.concat(all_domestic, ignore_index=True) if all_domestic else pd.DataFrame()
print(f"\n국내 ETF 수집 완료: {len(df_domestic)}행\n")

# 4. 해외 ETF 데이터 수집 (pykrx)

print("=" * 50)
print("해외 ETF 데이터 수집 중 (pykrx)...")
print("=" * 50)

# pykrx로 해외 ETF도 수집 (국내 상장 해외지수 ETF이므로 KRX에 상장됨)
overseas = df_filtered[df_filtered['구분2'] == '해외주식_지수'].copy()
all_overseas = []

for _, row in overseas.iterrows():
    ticker = row['티커_krx']
    name   = row['ETF명']
    try:
        df_ohlcv = stock.get_market_ohlcv_by_date(START_DATE, END_DATE, ticker)
        if df_ohlcv.empty:
            print(f"  [SKIP] {name} ({ticker}) - 데이터 없음")
            continue

        df_ohlcv = df_ohlcv.reset_index()
        df_ohlcv.columns = df_ohlcv.columns.str.strip()

        date_col = [c for c in df_ohlcv.columns if '날짜' in c or 'Date' in c or 'date' in c]
        if date_col:
            df_ohlcv = df_ohlcv.rename(columns={date_col[0]: 'Date'})
        else:
            df_ohlcv = df_ohlcv.rename(columns={df_ohlcv.columns[0]: 'Date'})

        df_ohlcv['티커']   = ticker
        df_ohlcv['ETF명']  = name
        df_ohlcv['구분']   = '해외주식_지수'
        df_ohlcv['통화']   = 'KRW'

        close_col = [c for c in df_ohlcv.columns if '종가' in c or 'Close' in c]
        if close_col:
            df_ohlcv['일별수익률'] = df_ohlcv[close_col[0]].pct_change()

        all_overseas.append(df_ohlcv)
        print(f"  [OK] {name} ({ticker}) - {len(df_ohlcv)}일")
        time.sleep(0.3)

    except Exception as e:
        print(f"  [ERR] {name} ({ticker}) - {e}")

df_overseas = pd.concat(all_overseas, ignore_index=True) if all_overseas else pd.DataFrame()
print(f"\n해외 ETF 수집 완료: {len(df_overseas)}행\n")

# 5. 통합 저장

df_all = pd.concat([df_domestic, df_overseas], ignore_index=True)

# 컬럼 정리
rename_map = {}
for col in df_all.columns:
    if '시가' in col:  rename_map[col] = '시가'
    elif '고가' in col: rename_map[col] = '고가'
    elif '저가' in col: rename_map[col] = '저가'
    elif '종가' in col: rename_map[col] = '종가'
    elif '거래량' in col: rename_map[col] = '거래량'
    elif '거래대금' in col: rename_map[col] = '거래대금'
    elif '기초지수' in col: rename_map[col] = '기초지수'
    elif 'NAV' in col: rename_map[col] = 'NAV'

df_all = df_all.rename(columns=rename_map)

# 티커 컬럼 찾아서 자동 처리
ticker_col = [c for c in df_all.columns if '티커' in c or 'ticker' in c.lower()][0]
print(f"티커 컬럼명: {ticker_col}")

aum_map = df_filtered.set_index('티커_krx')['AUM(억원)'].to_dict()
df_all['AUM(억원)'] = df_all[ticker_col].map(aum_map)

# 6. 수집 피처 요약 출력

print("=" * 50)
print("수집된 피처(컬럼) 목록:")
print("=" * 50)
for col in df_all.columns:
    print(f"  - {col}")
print()
print("수집 기간:", df_all['Date'].min(), "~", df_all['Date'].max())
print("종목 수:", df_all['티커'].nunique())
