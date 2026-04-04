from pathlib import Path
import pandas as pd

BASE_DIR = Path("/Users/user/Desktop/bitamin/Financial_project/geonho")
INPUT_PATH = BASE_DIR / "nyt_news_data" / "nyt_filtered_final.csv"
OUTPUT_PATH = BASE_DIR / "nyt_news_data" / "nyt_news_geonho.csv"

SECTION_MAP = {
    "nyt_domestic_bond_2019_2025": "domestic_bond",
    "nyt_overseas_bond_2019_2025": "overseas_bond",
    "nyt_real_assets_2019_2025": "real_assets",
}

def main():
    df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")
    df.columns = [str(col).strip() for col in df.columns]

    expected_cols = ["키워드", "날짜", "제목", "source_file"]
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"필수 컬럼 없음: {missing_cols} / 현재 컬럼: {df.columns.tolist()}")

    df = df[["키워드", "제목", "날짜", "source_file"]].copy()

    df = df.rename(columns={
        "키워드": "keyword",
        "제목": "title",
        "날짜": "date",
    })

    df["date"] = pd.to_datetime(df["date"], errors="coerce", format="mixed")
    df = df.dropna(subset=["date"]).reset_index(drop=True)

    df["keyword"] = df["keyword"].fillna("").astype(str).str.strip()
    df["title"] = df["title"].fillna("").astype(str).str.strip()
    df["section"] = df["source_file"].map(SECTION_MAP)

    if df["section"].isna().any():
        unknown = df.loc[df["section"].isna(), "source_file"].drop_duplicates().tolist()
        raise ValueError(f"section 매핑 안 된 source_file 있음: {unknown}")

    df = df[["keyword", "title", "date", "section"]].copy()

    df = df.drop_duplicates(subset=["title", "date"]).reset_index(drop=True)
    df = df.sort_values(["date", "section", "keyword", "title"]).reset_index(drop=True)

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"저장 완료: {OUTPUT_PATH}")
    print(f"행 개수: {len(df):,}")
    print("\nsection 분포")
    print(df["section"].value_counts())
    print("\n상위 10개 행")
    print(df.head(10).to_string(index=False))

if __name__ == "__main__":
    main()