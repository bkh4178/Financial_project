import pandas as pd
import numpy as np

# ── 입력 파일 경로 ──────────────────────────────────────────────────────────────
ETF_DOMESTIC_BOND = "../etf_data/etf_domestic_bond_close.csv"
ETF_FX_COMMODITY  = "../etf_data/etf_fx_commodity_close.csv"
ETF_GLOBAL_BOND   = "../etf_data/etf_global_bond_close.csv"
MK_SENTIMENT      = "../news_clean_ver/mk_sentiment_scored.csv"
NYT_SENTIMENT     = "../news_clean_ver/nyt_sentiment_scored.csv"

# ── 섹터별 티커 ─────────────────────────────────────────────────────────────────
SECTOR_ETF = {
    "sovereign_kr": ["A157450", "A148070", "A439870"],
    "sovereign_us": ["A329750", "A305080", "A453850"],
    "real_assets":  ["A411060", "A144600", "A261220", "A261240"],
}

# 티커 → 섹터 역매핑
TICKER_TO_SECTOR = {t: s for s, tickers in SECTOR_ETF.items() for t in tickers}

# ── 감성 섹션 매핑 ───────────────────────────────────────────────────────────────
DOMESTIC_SENTIMENT_MAP = {
    "sovereign_kr": "domestic_bond",
    "sovereign_us": "domestic_bond",
    "real_assets":  "real_assets",
}

NYT_SENTIMENT_MAP = {
    "sovereign_kr": "overseas_bond",
    "sovereign_us": "overseas_bond",
    "real_assets":  "real_assets",
}

# ── 1. ETF 패널 구성 ─────────────────────────────────────────────────────────────
etf_dom  = pd.read_csv(ETF_DOMESTIC_BOND)
etf_fx   = pd.read_csv(ETF_FX_COMMODITY)
etf_glob = pd.read_csv(ETF_GLOBAL_BOND)

etf = pd.concat([etf_dom, etf_fx, etf_glob], ignore_index=True)

# 컬럼 리네이밍
etf = etf.rename(columns={"티커": "ticker", "ETF명": "name", "AUM(억원)": "AUM", "종가": "end"})
etf["Date"] = pd.to_datetime(etf["Date"])
etf = etf.rename(columns={"Date": "date"})

# 대상 티커 필터링 및 섹터 부여
all_tickers = [t for tickers in SECTOR_ETF.values() for t in tickers]
etf = etf[etf["ticker"].isin(all_tickers)].copy()
etf["sector"] = etf["ticker"].map(TICKER_TO_SECTOR)

# target_5d: log(end_{t+5} / end_t)
etf = etf.sort_values(["ticker", "date"]).reset_index(drop=True)
etf["target_5d"] = etf.groupby("ticker")["end"].transform(
    lambda x: np.log(x.shift(-5) / x)
)

# ── 2. 국내 뉴스 감성 병합 ───────────────────────────────────────────────────────
mk = pd.read_csv(MK_SENTIMENT)
mk["date"] = pd.to_datetime(mk["date"])


def get_domestic_sentiment(etf_sector: str) -> pd.DataFrame:
    section = DOMESTIC_SENTIMENT_MAP[etf_sector]
    sub = mk[mk["section"] == section]
    agg = sub.groupby("date")["sentiment_score"].agg(
        domestic_mean="mean",
        domestic_std="std",
        domestic_count="count",
    ).reset_index()
    return agg


# ── 3. 해외 뉴스 감성 병합 ───────────────────────────────────────────────────────
nyt = pd.read_csv(NYT_SENTIMENT)
nyt["date"] = pd.to_datetime(nyt["date"])


def get_global_sentiment(etf_sector: str) -> pd.DataFrame:
    section = NYT_SENTIMENT_MAP[etf_sector]
    sub = nyt[nyt["section"] == section]
    agg = sub.groupby("date")["sentiment_score"].agg(
        global_mean="mean",
        global_std="std",
        global_count="count",
    ).reset_index()
    return agg


# ── 4. 섹터별 처리 및 저장 ──────────────────────────────────────────────────────
FINAL_COLS = [
    "date", "ticker", "name", "end", "AUM", "target_5d", "sector",
    "domestic_mean", "domestic_std", "domestic_count",
    "global_mean", "global_std", "global_count",
]

OUTPUT_FILES = {
    "sovereign_kr": "final_dataset_for_tft_sovereign_kr.csv",
    "sovereign_us": "final_dataset_for_tft_sovereign_us.csv",
    "real_assets":  "final_dataset_for_tft_realassets.csv",
}

for sector, out_file in OUTPUT_FILES.items():
    panel = etf[etf["sector"] == sector].copy()

    dom_sent = get_domestic_sentiment(sector)
    panel = panel.merge(dom_sent, on="date", how="left")

    glob_sent = get_global_sentiment(sector)
    panel = panel.merge(glob_sent, on="date", how="left")

    panel = panel[FINAL_COLS].sort_values("date").reset_index(drop=True)

    n = len(panel)
    t5_nan  = panel["target_5d"].isna().mean() * 100
    dom_nan = panel["domestic_mean"].isna().mean() * 100
    glo_nan = panel["global_mean"].isna().mean() * 100

    print(f"[{sector}]")
    print(f"  shape           : {panel.shape}")
    print(f"  target_5d NaN   : {t5_nan:.1f}%")
    print(f"  domestic_mean NaN: {dom_nan:.1f}%")
    print(f"  global_mean NaN : {glo_nan:.1f}%")
    print()

    panel.to_csv(out_file, index=False, encoding="utf-8-sig")
    print(f"  → saved: {out_file}\n")
