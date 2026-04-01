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

#%%
import pandas as pd
import glob

save_dir = "/Users/user/Desktop/bitamin/Financial_project/geonho/news"
files = glob.glob(f"{save_dir}/mk_news_*.csv")

count = []
summary = []

for f in files:
    df = pd.read_csv(f)

    # 파일명에서 키워드 추출
    keyword = f.split("mk_news_")[-1].replace(".csv", "")

    # 날짜 처리
    df['date'] = pd.to_datetime(df['date'], format='mixed').dt.date

    # 총 기사 수
    total_articles = len(df)

    # 날짜별 기사 수
    daily_counts = df.groupby('date').size()

    # 전체 기간 생성
    full_range = pd.date_range(df['date'].min(), df['date'].max()).date

    # 없는 날짜 찾기
    missing_dates = set(full_range) - set(daily_counts.index)

    # 결과 저장
    summary.append({
        'keyword': keyword,
        'total_articles': total_articles,
        'start_date': df['date'].min(),
        'end_date': df['date'].max(),
        'num_days': len(full_range),
        'missing_days': len(missing_dates),
        'avg_per_day': round(total_articles / len(full_range), 2)
    })

    print(f"\n=== {keyword} ===")
    print(f"총 기사 수: {total_articles}")
    print(f"기간: {df['date'].min()} ~ {df['date'].max()}")
    print(f"기사 없는 날 수: {len(missing_dates)}")
    print(f"하루 평균 기사 수: {round(total_articles / len(full_range), 2)}")

# 전체 요약 DataFrame
summary_df = pd.DataFrame(summary)
print("\n=== 전체 요약 ===")
print(summary_df.sort_values('total_articles', ascending=False))

#%%
