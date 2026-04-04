#%%
from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "nyt_news_data"
FILE_PATTERN = "nyt_*_2019_2025.csv"


def load_nyt_csvs(data_dir: Path = DATA_DIR, pattern: str = FILE_PATTERN) -> dict[str, pd.DataFrame]:
    """Load all NYT csv files matching the pattern.

    Expected columns:
    키워드, 날짜, 제목, 요약, URL
    """
    csv_paths = sorted(data_dir.glob(pattern))

    if not csv_paths:
        raise FileNotFoundError(
            f"No files matched pattern '{pattern}' in: {data_dir}"
        )

    dataframes: dict[str, pd.DataFrame] = {}

    for path in csv_paths:
        df = pd.read_csv(path, encoding="utf-8-sig")
        df.columns = [str(col).strip() for col in df.columns]

        expected_cols = ["키워드", "날짜", "제목", "요약", "URL"]
        missing_cols = [col for col in expected_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(
                f"{path.name}에 필요한 컬럼이 없음: {missing_cols} / 현재 컬럼: {df.columns.tolist()}"
            )

        df = df[["키워드", "날짜", "제목", "요약", "URL"]].copy()
        df["날짜"] = (
            df["날짜"]
            .astype(str)
            .str.strip()
            .str.replace("Sept.", "Sep", regex=False)
            .str.replace(r"([A-Za-z]{3})\.", r"\1", regex=True)
        )

        df["날짜"] = pd.to_datetime(df["날짜"], format="mixed", errors="coerce")

        for col in ["키워드", "제목", "요약", "URL"]:
            df[col] = df[col].fillna("").astype(str).str.strip()

        dataframes[path.stem] = df

    return dataframes


def preview_loaded_data(dataframes: dict[str, pd.DataFrame]) -> None:
    for name, df in dataframes.items():
        print(f"\n{'=' * 80}")
        print(f"FILE: {name}")
        print(f"rows={len(df):,}, cols={len(df.columns)}")
        print(df[["키워드", "날짜", "제목", "요약", "URL"]].head(3))
        print("missing summary:", (df["요약"] == "").sum())
        print("invalid date:", df["날짜"].isna().sum())
        print("duplicate (title, date):", df.duplicated(subset=["제목", "날짜"]).sum())


nyt_dfs = load_nyt_csvs()
preview_loaded_data(nyt_dfs)

#%%
# 3개 csv 합치기
all_dfs = []
for name, df in nyt_dfs.items():
    temp = df.copy()
    temp["source_file"] = name
    all_dfs.append(temp)

df_all = pd.concat(all_dfs, ignore_index=True)

print("전체 shape:", df_all.shape)
print(df_all.head())

#%%
# 중복 확인
print("URL 중복:", df_all.duplicated(subset=["URL"]).sum())
print("제목+날짜 중복:", df_all.duplicated(subset=["제목", "날짜"]).sum())
print("제목+요약+날짜 중복:", df_all.duplicated(subset=["제목", "요약", "날짜"]).sum())

#%%
# 중복 제거
print("중복 제거 전:", len(df_all))

df_all = df_all.drop_duplicates(subset=["URL"]).reset_index(drop=True)
print("URL 중복 제거 후:", len(df_all))

df_all = df_all.drop_duplicates(subset=["제목", "날짜"]).reset_index(drop=True)
print("제목+날짜 중복 제거 후:", len(df_all))

#%%
# 요약 분포 확인
print(df_all["요약"].value_counts().head(50))
print(df_all["요약"].str.len().describe())

#%%
# summary 1차 필터링
exclude_summary = [
    "THE DAILY",
    "MUSIC",
    "MOVIES",
    "THE LEARNING NETWORK",
    "TELEVISION",
    "SPORTS",
    "ARTS",
    "LETTERS",
    "SOCCER",
    "BOOKS",
    "THEATER",
    "OBITUARIES",
    "OLYMPICS",
    "BASEBALL",
    "FASHION",
    "STYLE",
    "MAGAZINE",
    "TRAVEL",
    "T MAGAZINE",
    "FOOD",
    "BOOK REVIEW",
    "PODCASTS",
    "LOVE",
    "ART & DESIGN",
    "FAMILY",
    "EAT",
    "SELF-CARE",
    "AT HOME",
    "WELL",
]

df_filtered = df_all[~df_all["요약"].isin(exclude_summary)].reset_index(drop=True)

print("summary 1차 필터 전:", len(df_all))
print("summary 1차 필터 후:", len(df_filtered))
print(f"summary 1차 제거 비율: {(1 - len(df_filtered) / len(df_all)) * 100:.2f}%")
print(df_filtered["요약"].value_counts().head(50))

#%%
for sec in ["CLIMATE", "HEALTH"]:
    print(f"\n===== {sec} =====")
    temp = df_filtered[df_filtered["요약"] == sec]
    print(temp[["날짜", "키워드", "제목"]].sample(min(20, len(temp)), random_state=42))

#%%
exclude_summary += ["HEALTH","COLLEGE BASKETBALL", "SKIING","TENNIS","GOLF","N.F.L.",'DANCE','WINE, BEER & COCKTAILS']

df_filtered = df_all[~df_all["요약"].isin(exclude_summary)].reset_index(drop=True)

print("summary 1차 필터 전:", len(df_all))
print("summary 1차 필터 후:", len(df_filtered))
print(f"summary 1차 제거 비율: {(1 - len(df_filtered) / len(df_all)) * 100:.2f}%")
print(df_filtered["요약"].value_counts().head(50))


#%%
for sec in ["REAL ESTATE", "NEW YORK"]:
    print(f"\n===== {sec} =====")
    temp = df_filtered[df_filtered["요약"] == sec]
    print(temp[["날짜", "키워드", "제목"]].sample(min(20, len(temp)), random_state=42))

#%%
exclude_summary += ["REAL ESTATE", "NEW YORK"]

df_filtered = df_all[~df_all["요약"].isin(exclude_summary)].reset_index(drop=True)

print("summary 1차 필터 전:", len(df_all))
print("summary 1차 필터 후:", len(df_filtered))
print(f"summary 1차 제거 비율: {(1 - len(df_filtered) / len(df_all)) * 100:.2f}%")
print(df_filtered["요약"].value_counts().head(50))

#%%
for sec in ["WORLD", "U.S.",'ASIA PACIFIC']:
    print(f"\n===== {sec} =====")
    temp = df_filtered[df_filtered["요약"] == sec]
    print(temp[["날짜", "키워드", "제목"]].sample(min(20, len(temp)), random_state=42))

#%%
exclude_summary += ["U.S.", 'WORLD']

df_filtered = df_all[~df_all["요약"].isin(exclude_summary)].reset_index(drop=True)

print("summary 1차 필터 전:", len(df_all))
print("summary 1차 필터 후:", len(df_filtered))
print(f"summary 1차 제거 비율: {(1 - len(df_filtered) / len(df_all)) * 100:.2f}%")
print(df_filtered["요약"].value_counts().head(50))

#%%
# 제목 2차 필터링: WORLD, ASIA PACIFIC는 남겨두고 제목 기준으로 점검
for sec in ["BRIEFING"]:
    print(f"\n===== {sec} 제목 샘플 =====")
    temp = df_filtered[df_filtered["요약"] == sec]
    print(temp[["날짜", "키워드", "제목", "요약"]].sample(min(30, len(temp)), random_state=42))



#%%
'''
위 단계에서 summary기준 너무 잡음이 큰 요약은 필터링
이때 애매한 summary는 샘플링해서 제목과 키워드를 기준으로 확인 -> us, world, real estate, new york etc

잡음이 조금 존재하지만 통째로 버리긴 아까운 summary : BRIEFING, ASIA PACIFIC, OPINION

'''


#%%
# BRIEFING 제목 2차 필터링 실험
briefing_df = df_filtered[df_filtered["요약"] == "BRIEFING"].copy()
briefing_df["제목_lc"] = briefing_df["제목"].str.lower().str.strip()

briefing_pattern = (
    r"(^your\s.+briefing$)|"
    r"(^monday\sbriefing)|(^tuesday\sbriefing)|(^wednesday\sbriefing)|"
    r"(^thursday\sbriefing)|(^friday\sbriefing)|(^saturday\sbriefing)|(^sunday\sbriefing)|"
    r"(^the\sevening$)|(^your\sevening\sbriefing$)|(^evening\sbriefing$)|"
    r"(\bbriefing\b)"
)

market_keep_pattern = (
    r"(inflation|oil|economy|economic|market|markets|treasury|treasuries|yield|yields|"
    r"bond|bonds|fed|rate|rates|tariff|tariffs|trade|gas|stock|stocks|dollar|currency|"
    r"crude|grain|recession|sanction|sanctions|energy|prices?)"
)

briefing_generic_mask = briefing_df["제목_lc"].str.contains(briefing_pattern, regex=True, na=False)
briefing_market_keep_mask = briefing_df["제목_lc"].str.contains(market_keep_pattern, regex=True, na=False)
briefing_drop_mask = briefing_generic_mask & ~briefing_market_keep_mask

print("BRIEFING 전체 개수:", len(briefing_df))
print("BRIEFING 포맷형 제목 개수:", int(briefing_generic_mask.sum()))
print("BRIEFING 예외 유지 개수:", int(briefing_market_keep_mask.sum()))
print("BRIEFING 제거 후보 개수:", int(briefing_drop_mask.sum()))
print(f"BRIEFING 제거 후보 비율: {briefing_drop_mask.mean() * 100:.2f}%")

print("\n===== BRIEFING 제거 후보 샘플 =====")
print(
    briefing_df.loc[briefing_drop_mask, ["날짜", "키워드", "제목", "요약"]]
    .sample(min(30, int(briefing_drop_mask.sum())), random_state=42)
)

print("\n===== BRIEFING 예외 유지 샘플 =====")
print(
    briefing_df.loc[briefing_generic_mask & briefing_market_keep_mask, ["날짜", "키워드", "제목", "요약"]]
    .sample(min(30, int((briefing_generic_mask & briefing_market_keep_mask).sum())), random_state=42)
)

briefing_title_drop_idx = briefing_df.loc[briefing_drop_mask].index

df_filtered_briefing = df_filtered.drop(index=briefing_title_drop_idx).reset_index(drop=True)

print("\nBRIEFING 제목 필터 전:", len(df_filtered))
print("BRIEFING 제목 필터 후:", len(df_filtered_briefing))
print(f"BRIEFING 제목 필터 제거 비율: {(1 - len(df_filtered_briefing) / len(df_filtered)) * 100:.2f}%")
print(df_filtered_briefing["요약"].value_counts().head(50))
df_filtered = df_filtered_briefing.copy()

#%%
#%%
'''
위 단계에서 summary기준 너무 잡음이 큰 요약은 필터링
이때 애매한 summary는 샘플링해서 제목과 키워드를 기준으로 확인 -> us, world, real estate, new york etc

잡음이 조금 존재하지만 통째로 버리긴 아까운 summary : BRIEFING, ASIA PACIFIC, OPINION
'''

# BRIEFING 제목 2차 필터링 실험
briefing_df = df_filtered[df_filtered["요약"] == "BRIEFING"].copy()
briefing_df["제목_lc"] = briefing_df["제목"].str.lower().str.strip()

briefing_pattern = (
    r"(^your\s.+briefing$)|"
    r"(^monday\sbriefing)|(^tuesday\sbriefing)|(^wednesday\sbriefing)|"
    r"(^thursday\sbriefing)|(^friday\sbriefing)|(^saturday\sbriefing)|(^sunday\sbriefing)|"
    r"(^the\sevening$)|(^your\sevening\sbriefing$)|(^evening\sbriefing$)|"
    r"(\bbriefing\b)"
)

market_keep_pattern = (
    r"(inflation|oil|economy|economic|market|markets|treasury|treasuries|yield|yields|"
    r"bond|bonds|fed|rate|rates|tariff|tariffs|trade|gas|stock|stocks|dollar|currency|"
    r"crude|grain|recession|sanction|sanctions|energy|prices?)"
)

briefing_generic_mask = briefing_df["제목_lc"].str.contains(briefing_pattern, regex=True, na=False)
briefing_market_keep_mask = briefing_df["제목_lc"].str.contains(market_keep_pattern, regex=True, na=False)
briefing_drop_mask = briefing_generic_mask & ~briefing_market_keep_mask

print("BRIEFING 전체 개수:", len(briefing_df))
print("BRIEFING 포맷형 제목 개수:", int(briefing_generic_mask.sum()))
print("BRIEFING 예외 유지 개수:", int(briefing_market_keep_mask.sum()))
print("BRIEFING 제거 후보 개수:", int(briefing_drop_mask.sum()))
print(f"BRIEFING 제거 후보 비율: {briefing_drop_mask.mean() * 100:.2f}%")

print("\n===== BRIEFING 제거 후보 샘플 =====")
if int(briefing_drop_mask.sum()) > 0:
    print(
        briefing_df.loc[briefing_drop_mask, ["날짜", "키워드", "제목", "요약"]]
        .sample(min(30, int(briefing_drop_mask.sum())), random_state=42)
    )
else:
    print("없음")

print("\n===== BRIEFING 예외 유지 샘플 =====")
briefing_keep_mask = briefing_generic_mask & briefing_market_keep_mask
if int(briefing_keep_mask.sum()) > 0:
    print(
        briefing_df.loc[briefing_keep_mask, ["날짜", "키워드", "제목", "요약"]]
        .sample(min(30, int(briefing_keep_mask.sum())), random_state=42)
    )
else:
    print("없음")

briefing_title_drop_idx = briefing_df.loc[briefing_drop_mask].index

df_filtered_briefing = df_filtered.drop(index=briefing_title_drop_idx).reset_index(drop=True)

print("\nBRIEFING 제목 필터 전:", len(df_filtered))
print("BRIEFING 제목 필터 후:", len(df_filtered_briefing))
print(f"BRIEFING 제목 필터 제거 비율: {(1 - len(df_filtered_briefing) / len(df_filtered)) * 100:.2f}%")
print(df_filtered_briefing["요약"].value_counts().head(50))

# 다음 단계부터는 briefing 필터 반영본 사용
df_filtered = df_filtered_briefing.copy()

#%%
# ASIA PACIFIC 제목 2차 필터링 실험: 일단 버릴 것만 제거하고 다시 샘플링
asia_df = df_filtered[df_filtered["요약"] == "ASIA PACIFIC"].copy()
asia_df["제목_lc"] = asia_df["제목"].str.lower().str.strip()

asia_drop_pattern = (
    r"(covid|coronavirus|vaccine|vaccination|outbreak|quarantine|lockdown|"
    r"protest|protests|abortion|criminal|crime|murder|death|deaths|"
    r"lost weight|silence|first coronavirus death|booking system|"
    r"most notorious|health)"
)
asia_small_drop_pattern = (
    r"(apologizes|photographer|dies\\b|bombing|kills\\b|earthquake|"
    r"latest developments|same-sex|buddhist statue|"
    r"tell me who my mother is|families demand answers|construction site|"
    r"talent agency)"
)


asia_drop_mask = (
    asia_df["제목_lc"].str.contains(asia_drop_pattern, regex=True, na=False)
    | asia_df["제목_lc"].str.contains(asia_small_drop_pattern, regex=True, na=False)
)

print("ASIA PACIFIC 전체 개수:", len(asia_df))
print("ASIA PACIFIC 제거 후보 개수:", int(asia_drop_mask.sum()))
print(f"ASIA PACIFIC 제거 후보 비율: {asia_drop_mask.mean() * 100:.2f}%")

print("\n===== ASIA PACIFIC 제거 후보 샘플 =====")
if int(asia_drop_mask.sum()) > 0:
    print(
        asia_df.loc[asia_drop_mask, ["날짜", "키워드", "제목", "요약"]]
        .sample(min(30, int(asia_drop_mask.sum())), random_state=42)
    )
else:
    print("없음")

asia_title_drop_idx = asia_df.loc[asia_drop_mask].index

df_filtered_asia = df_filtered.drop(index=asia_title_drop_idx).reset_index(drop=True)

print("\nASIA PACIFIC 제목 필터 전:", len(df_filtered))
print("ASIA PACIFIC 제목 필터 후:", len(df_filtered_asia))
print(f"ASIA PACIFIC 제목 필터 제거 비율: {(1 - len(df_filtered_asia) / len(df_filtered)) * 100:.2f}%")

print("\n===== ASIA PACIFIC 필터 후 제목 샘플 =====")
asia_left = df_filtered_asia[df_filtered_asia["요약"] == "ASIA PACIFIC"]
if len(asia_left) > 0:
    print(
        asia_left[["날짜", "키워드", "제목", "요약"]]
        .sample(min(30, len(asia_left)), random_state=38)
    )
else:
    print("없음")

# 필요하면 다음 단계부터 이걸 기준으로 사용
df_filtered = df_filtered_asia.copy()

#%%

#%%
# OPINION / SUNDAY OPINION 제목 2차 필터링: 유지 키워드가 있는 것만 유지
opinion_sections = ["OPINION", "SUNDAY OPINION"]
opinion_df = df_filtered[df_filtered["요약"].isin(opinion_sections)].copy()
opinion_df["제목_lc"] = opinion_df["제목"].str.lower().str.strip()

opinion_keep_pattern = (
    r"(inflation|fed|federal reserve|interest rate|rates|bond|bonds|yield|yields|"
    r"treasury|treasuries|trade|tariff|tariffs|economy|economic|market|markets|"
    r"tax|taxes|recession|fracking|oil|gas|energy|pipeline|housing|home|homes|"
    r"rent|rents|mortgage|mortgages|china|sanction|sanctions|dollar|currency|"
    r"billionaire|billionaires|invest|investing|investment|supply chain|epa|"
    r"nuclear power|population)"
)

opinion_keep_mask = opinion_df["제목_lc"].str.contains(opinion_keep_pattern, regex=True, na=False)
opinion_drop_mask = ~opinion_keep_mask

print("OPINION/SUNDAY OPINION 전체 개수:", len(opinion_df))
print("유지 개수:", int(opinion_keep_mask.sum()))
print("제거 후보 개수:", int(opinion_drop_mask.sum()))
print(f"제거 후보 비율: {opinion_drop_mask.mean() * 100:.2f}%")

print("\n===== OPINION/SUNDAY OPINION 제거 후보 샘플 =====")
if int(opinion_drop_mask.sum()) > 0:
    print(
        opinion_df.loc[opinion_drop_mask, ["날짜", "키워드", "제목", "요약"]]
        .sample(min(30, int(opinion_drop_mask.sum())), random_state=42)
    )
else:
    print("없음")

print("\n===== OPINION/SUNDAY OPINION 유지 샘플 =====")
if int(opinion_keep_mask.sum()) > 0:
    print(
        opinion_df.loc[opinion_keep_mask, ["날짜", "키워드", "제목", "요약"]]
        .sample(min(30, int(opinion_keep_mask.sum())), random_state=42)
    )
else:
    print("없음")

opinion_title_drop_idx = opinion_df.loc[opinion_drop_mask].index

df_filtered_opinion = df_filtered.drop(index=opinion_title_drop_idx).reset_index(drop=True)

print("\nOPINION 제목 필터 전:", len(df_filtered))
print("OPINION 제목 필터 후:", len(df_filtered_opinion))
print(f"OPINION 제목 필터 제거 비율: {(1 - len(df_filtered_opinion) / len(df_filtered)) * 100:.2f}%")

# 다음 단계부터 opinion 필터 반영본 사용
df_filtered = df_filtered_opinion.copy()

#%%
# OPINION | THE WORLD, OPINION | ENVIRONMENT는 그대로 샘플 확인
for sec in ["OPINION | THE WORLD", "OPINION | ENVIRONMENT"]:
    print(f"\n===== {sec} 제목 샘플 =====")
    temp = df_filtered[df_filtered["요약"] == sec]
    if len(temp) > 0:
        print(temp[["날짜", "키워드", "제목", "요약"]].sample(min(30, len(temp)), random_state=42))
    else:
        print("없음")

#%%
# 현재 단계 최종 summary 분포 확인
print("\n===== 현재 df_filtered 기준 summary 분포 =====")
print(df_filtered["요약"].value_counts().head(80))
print("\n현재 행 개수:", len(df_filtered))
print(df_filtered["요약"].value_counts().head(80).to_string())

#%%
'''
HOME & GARDEN, 
MEN’S STYLE                          1
MORTGAGES                            1
PREGNANCY  
WIRECUTTER                           1
HORSE RACING   
AUTO RACING                          2
ENTREPRENEURSHIP                     2
HOCKEY   
COLLEGE FOOTBALL  
GAMEPLAY                            20
BASKETBALL   
'''

exclude_summary += [
    "HOME & GARDEN",
    "MEN’S STYLE",
    "PREGNANCY",
    "WIRECUTTER",
    "HORSE RACING",
    "AUTO RACING",
    "HOCKEY",
    "COLLEGE FOOTBALL",
    "GAMEPLAY",
    "BASKETBALL",
    "ENTREPRENEURSHIP",
]
df_filtered = df_filtered[~df_filtered["요약"].isin(exclude_summary)].reset_index(drop=True)

print("summary 1차 필터 전:", len(df_all))
print("summary 1차 필터 후:", len(df_filtered))
print(f"summary 1차 제거 비율: {(1 - len(df_filtered) / len(df_all)) * 100:.2f}%")
print(df_filtered["요약"].value_counts().head(50))

#%%
# 최종 저장
save_path = DATA_DIR / "nyt_filtered_final_2019_2025.csv"
df_filtered.to_csv(save_path, index=False, encoding="utf-8-sig")
print(f"\n저장 완료: {save_path}")
#%%
print(df_filtered.sample(30, random_state=42)[["날짜", "키워드", "제목", "요약"]].to_string())