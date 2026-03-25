#%%
# 데이터 누락 확인 (세세하게 말고 크게 확인 용도)
import pandas as pd
import glob

save_dir = "/Users/user/Desktop/bitamin/Financial_project/geonho/news"
files = glob.glob(f"{save_dir}/mk_news_*.csv")

def plot(f):
    print(f)
    df = pd.read_csv(f)
    df['date'] = pd.to_datetime(df['date'], format='mixed').dt.date
    df = df.sort_values('date')
    df.groupby('date').size().plot()
    print(len(df))

#%%
plot(files[6])

#%%
# 날짜 정렬 + 중복 제거 용도
import pandas as pd
import glob

save_dir = "/Users/user/Desktop/bitamin/Financial_project/geonho/news"
files = glob.glob(f"{save_dir}/mk_news_*.csv")

def sort_and_drop_dup(files):
    for f in files:
        df = pd.read_csv(f)
        df['date'] = pd.to_datetime(df['date'], format='mixed').dt.date
        df.drop(columns=['Unnamed: 0'], inplace=True)
        df = df.drop_duplicates(['title','date'])
        df = df.sort_values("date").reset_index(drop=True)
        df.to_csv(f, index=False)
        print(f,len(df), '\n')

sort_and_drop_dup(files)

#%%
keyword = ['인플레이션','연준','경기침체']
dir = '/Users/user/Desktop/bitamin/Financial_project/geonho/news'

def sort_and_drop_dup2(keyword : list, dir : str):
    for k in keyword:
        new_dir = dir+f'/mk_news_{k}.csv'
        df = pd.read_csv(new_dir)
        df['date'] = pd.to_datetime(df['date'], format='mixed').dt.date
        df = df.drop_duplicates(['title','date'])
        df = df.sort_values("date").reset_index(drop=True)
        df.to_csv(new_dir, index=False)
        print(f'mk_news_{k}',len(df), '\n')
sort_and_drop_dup2(keyword, dir)