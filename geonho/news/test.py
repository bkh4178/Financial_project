#%%
# 누락 기간 데이터 확인
import pandas as pd
keyword = '기준금리'
df = pd.read_csv(f'mk_news_{keyword}.csv')
df["date"] = pd.to_datetime(df["date"], format="mixed").dt.date
df = df.sort_values("date")
df.groupby("date").size().plot()


#%%
# python crawl_news2.py --keywords 국채 --start_date 2021-01-01 --end_date 2021-07-01
keyword = '국채'
df = pd.read_csv(f'mk_news_{keyword}.csv')
df["date"] = pd.to_datetime(df["date"], format="mixed").dt.date
df = df.sort_values("date")
df.groupby("date").size().plot()