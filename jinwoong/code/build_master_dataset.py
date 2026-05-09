"""
마스터 데이터셋 빌드
- 6개 ETF × 영업일 일별 패널
- 가격 데이터 + 감성 피처 + target_5d (5거래일 선행 로그수익률)

입력:
  data/raw/etf/etf_price_data.csv
  data/sentiment/sentiment_table.csv
출력:
  data/final/master_dataset.csv
"""
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

ETF_SECTOR = {
    "069500": "domestic_core",   # KODEX 200
    "229200": "domestic_core",   # KODEX 코스닥150
    "360750": "global_macro",    # TIGER 미국S&P500
    "133690": "global_macro",    # TIGER 미국나스닥100
    "241180": "global_macro",    # TIGER 일본니케이225
    "251350": "global_macro",    # KODEX 선진국MSCI World
}


def main():
    # 1. 가격 데이터 로드 및 필터링
    price = pd.read_csv(
        BASE_DIR / "data/raw/etf/etf_price_data.csv",
        encoding="utf-8-sig",
        dtype={"티커": str},
    )
    price.columns = price.columns.str.strip()
    price = price[price["티커"].isin(ETF_SECTOR)].copy()

    price = price.rename(columns={
        "Date":     "date",
        "티커":     "ticker",
        "ETF명":    "name",
        "종가":     "end",
        "AUM(억원)": "AUM",
    })
    price["date"]   = pd.to_datetime(price["date"])
    price["sector"] = price["ticker"].map(ETF_SECTOR)
    price = (
        price[["date", "ticker", "name", "end", "AUM", "sector"]]
        .sort_values(["date", "ticker"])
        .reset_index(drop=True)
    )
    print(f"가격 데이터: {len(price):,}행")

    # 2. target_5d = log(P_{t+5} / P_t) — ticker별 계산
    price["target_5d"] = (
        price.groupby("ticker")["end"]
        .transform(lambda x: np.log(x.shift(-5) / x))
    )

    # 3. 감성 테이블 로드
    sent = pd.read_csv(
        BASE_DIR / "data/sentiment/sentiment_table.csv",
        encoding="utf-8-sig",
    )
    sent["date"] = pd.to_datetime(sent["date"])
    sent = sent.rename(columns={"section": "sector"})
    print(f"감성 테이블: {len(sent):,}행")

    # 4. VIX 데이터 로드
    vix = pd.read_csv(
        BASE_DIR / "data/raw/vix/vix_daily.csv",
        encoding="utf-8-sig",
    )
    vix["date"] = pd.to_datetime(vix["Date"])
    vix = vix.rename(columns={"Close": "vix_close"})[["date", "vix_close"]]

    # 5. (date, sector) 기준 left join → VIX join
    master = price.merge(sent, on=["date", "sector"], how="left")
    master = master.merge(vix, on="date", how="left")

    # 기사 1건인 날 std=NaN → 0으로 (기사 없는 날은 NaN 유지)
    master.loc[master["domestic_count"] == 1, "domestic_std"] = 0.0
    master.loc[master["global_count"]   == 1, "global_std"]   = 0.0

    # 6. 컬럼 순서
    master = master[[
        "date", "ticker", "name", "end", "AUM", "target_5d", "sector",
        "domestic_mean", "domestic_std", "domestic_count",
        "global_mean",   "global_std",   "global_count",
        "vix_close",
    ]]

    # 6. 저장
    out = BASE_DIR / "data/final/master_dataset.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    master.to_csv(out, index=False, encoding="utf-8-sig")

    print(f"\nshape: {master.shape}")
    print(f"저장: {out}")

    print("\n티커별 행 수:")
    print(master.groupby("ticker")["date"].agg(["count", "min", "max"]))

    print("\n결측치 현황:")
    print(master.isnull().sum())

    print("\n샘플 (첫 3행):")
    print(master.head(3).to_string())


if __name__ == "__main__":
    main()
