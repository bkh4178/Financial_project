from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
INPUT_PATH  = BASE_DIR / "data/processed/nyt_news/nyt_final.csv"
OUTPUT_PATH = BASE_DIR / "data/processed/nyt_news/nyt_news_preprocessed.csv"

# NYT 키워드 → section 매핑
SECTION_MAP = {
    "KOSPI":        "domestic_core",
    "KOSDAQ":       "domestic_core",
    "S&P 500":      "global_macro",
    "Nasdaq 100":   "global_macro",
    "Dow Jones":    "global_macro",
    "Russell 2000": "global_macro",
    "Nikkei 225":   "global_macro",
    "Euro Stoxx 50":"global_macro",
    "DAX":          "global_macro",
    "MSCI World":   "global_macro",
    "MSCI ACWI":    "global_macro",
    "MSCI EAFE":    "global_macro",
}


def main() -> None:
    df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig", dtype=str)
    df.columns = [c.strip() for c in df.columns]

    # 날짜 파싱 (NYT는 별도 clean_title 불필요)
    df["date"] = pd.to_datetime(df["date"], errors="coerce", format="mixed")
    df = df.dropna(subset=["date"]).reset_index(drop=True)

    # 빈 제목 제거
    df["title"] = df["title"].fillna("").str.strip()
    df = df[df["title"] != ""].reset_index(drop=True)

    # section 매핑
    df["section"] = df["keyword"].map(SECTION_MAP)
    unmapped = df[df["section"].isna()]["keyword"].unique().tolist()
    if unmapped:
        raise ValueError(f"section 매핑 안 된 keyword: {unmapped}")

    # source 추가
    df["source"] = "NYT"

    # 중복 제거
    df = df.drop_duplicates(subset=["title", "date"]).reset_index(drop=True)

    # 정렬 및 컬럼 순서 정리
    df = df[["date", "source", "section", "keyword", "title"]]
    df = df.sort_values(["date", "section", "keyword"]).reset_index(drop=True)

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"저장 완료: {OUTPUT_PATH}")
    print(f"행 수: {len(df):,}")
    print("\nsection 분포:")
    print(df["section"].value_counts().to_string())
    print("\n상위 5행:")
    print(df.head().to_string(index=False))


if __name__ == "__main__":
    main()
