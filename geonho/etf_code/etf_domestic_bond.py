import time
import warnings
from pathlib import Path

import pandas as pd
from pykrx import stock

warnings.filterwarnings("ignore")

# ============================================================
# 설정
# ============================================================
START_DATE = "20190101"
END_DATE = "20251231"

PROJECT_ROOT = Path("/Users/user/Desktop/bitamin/Financial_project")
INPUT_XLSX = PROJECT_ROOT / "geonho" / "data" / "주식종목리스트.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "geonho" / "data"
OUTPUT_PATH = OUTPUT_DIR / "etf_domestic_bond_close.csv"

SHEET_NAME = "ETF (187)"
HEADER_ROW = 3

# 구분2 기준: 국내채권만 사용
INCLUDE_CATEGORIES = ["국내채권_회사채", "국내채권_종합"]

# pykrx 과부하 방지
REQUEST_SLEEP = 0.3


# ============================================================
# 유틸 함수
# ============================================================

def load_etf_universe(xlsx_path: Path) -> pd.DataFrame:
    """엑셀에서 ETF 유니버스를 불러와 필요한 컬럼만 정리한다."""
    df = pd.read_excel(xlsx_path, sheet_name=SHEET_NAME, header=HEADER_ROW)
    df.columns = ["drop", "티커", "ETF명", "AUM(억원)", "기초지수", "구분1", "구분2"]

    df = df.drop(columns=["drop"]).dropna(subset=["티커"]).copy()
    df = df[df["티커"] != "티커"].copy()
    df["AUM(억원)"] = pd.to_numeric(df["AUM(억원)"], errors="coerce")

    # 국내채권만 필터링
    df = df[df["구분2"].isin(INCLUDE_CATEGORIES)].copy().reset_index(drop=True)

    # pykrx용 6자리 코드
    df["티커_krx"] = df["티커"].astype(str).str.replace("A", "", regex=False)

    # 러프한 서브섹터 규칙
    # 국내채권_회사채 -> credit
    # 국내채권_종합   -> government
    df["sector_main"] = "korea_bond"
    df["sector_sub"] = df["구분2"].map({
        "국내채권_회사채": "credit",
        "국내채권_종합": "government",
    })

    return df



def standardize_price_frame(df_ohlcv: pd.DataFrame, row: pd.Series) -> pd.DataFrame:
    """pykrx OHLCV 결과에서 필요한 컬럼만 남겨 표준화한다."""
    df_ohlcv = df_ohlcv.reset_index().copy()
    df_ohlcv.columns = df_ohlcv.columns.str.strip()

    # 날짜 컬럼명 통일
    date_candidates = [c for c in df_ohlcv.columns if "날짜" in c or "Date" in c or "date" in c]
    if date_candidates:
        df_ohlcv = df_ohlcv.rename(columns={date_candidates[0]: "Date"})
    else:
        df_ohlcv = df_ohlcv.rename(columns={df_ohlcv.columns[0]: "Date"})

    # 종가 컬럼 찾기
    close_candidates = [c for c in df_ohlcv.columns if "종가" in c or "Close" in c]
    if not close_candidates:
        raise ValueError("종가 컬럼을 찾지 못했습니다.")

    close_col = close_candidates[0]

    df_out = df_ohlcv[["Date", close_col]].copy()
    df_out = df_out.rename(columns={close_col: "종가"})

    df_out["Date"] = pd.to_datetime(df_out["Date"]).dt.normalize()
    df_out["티커"] = row["티커"]
    df_out["ETF명"] = row["ETF명"]
    df_out["구분1"] = row["구분1"]
    df_out["구분2"] = row["구분2"]
    df_out["sector_main"] = row["sector_main"]
    df_out["sector_sub"] = row["sector_sub"]
    df_out["기초지수"] = row["기초지수"]
    df_out["AUM(억원)"] = row["AUM(억원)"]

    # 일별 수익률도 같이 저장해두면 나중에 편하다
    df_out["일별수익률"] = df_out["종가"].pct_change()

    return df_out[[
        "Date",
        "티커",
        "ETF명",
        "구분1",
        "구분2",
        "sector_main",
        "sector_sub",
        "기초지수",
        "AUM(억원)",
        "종가",
        "일별수익률",
    ]]



def collect_domestic_bond_prices(df_universe: pd.DataFrame) -> pd.DataFrame:
    """국내채권 ETF 종가 데이터를 pykrx로 수집한다."""
    collected = []

    print("=" * 60)
    print("국내채권 ETF 종가 수집 시작")
    print(f"수집 기간: {START_DATE} ~ {END_DATE}")
    print(f"대상 종목 수: {len(df_universe)}개")
    print("=" * 60)

    for idx, row in df_universe.iterrows():
        ticker_krx = row["티커_krx"]
        etf_name = row["ETF명"]
        sector_sub = row["sector_sub"]

        try:
            df_ohlcv = stock.get_market_ohlcv_by_date(START_DATE, END_DATE, ticker_krx)
            if df_ohlcv.empty:
                print(f"[{idx+1}/{len(df_universe)}] [SKIP] {etf_name} ({ticker_krx}) - 데이터 없음")
                continue

            df_out = standardize_price_frame(df_ohlcv, row)
            collected.append(df_out)
            print(
                f"[{idx+1}/{len(df_universe)}] [OK] {etf_name} ({ticker_krx}) "
                f"- {len(df_out)}일 / {sector_sub}"
            )
            time.sleep(REQUEST_SLEEP)

        except Exception as e:
            print(f"[{idx+1}/{len(df_universe)}] [ERR] {etf_name} ({ticker_krx}) - {e}")

    if not collected:
        return pd.DataFrame(columns=[
            "Date", "티커", "ETF명", "구분1", "구분2", "sector_main", "sector_sub",
            "기초지수", "AUM(억원)", "종가", "일별수익률"
        ])

    df_all = pd.concat(collected, ignore_index=True)
    df_all = df_all.sort_values(["티커", "Date"]).reset_index(drop=True)
    return df_all


# ============================================================
# 실행
# ============================================================
if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_XLSX.exists():
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {INPUT_XLSX}")

    df_universe = load_etf_universe(INPUT_XLSX)

    print("국내채권 ETF 분류 요약")
    print(df_universe[["티커", "ETF명", "구분2", "sector_sub"]].to_string(index=False))
    print()

    df_prices = collect_domestic_bond_prices(df_universe)

    print("\n" + "=" * 60)
    print("수집 결과 요약")
    print("=" * 60)
    print(f"행 수: {len(df_prices):,}")
    print(f"종목 수: {df_prices['티커'].nunique() if not df_prices.empty else 0}")

    if not df_prices.empty:
        print(f"날짜 범위: {df_prices['Date'].min().date()} ~ {df_prices['Date'].max().date()}")
        print("서브섹터별 종목 수:")
        print(df_universe.groupby("sector_sub")["티커"].nunique())

    df_prices.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\n저장 완료: {OUTPUT_PATH}")
