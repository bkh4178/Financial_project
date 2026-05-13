from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "mk_news_data"
OUTPUT_PATH = DATA_DIR / "mk_news_geonho.csv"

# 거시 변수로 따로 쓰는 파일은 제외
EXCLUDE_KEYWORDS = {"인플레이션", "경기침체", "연준"}

# 파일명 suffix -> section 매핑
SECTION_MAP = {
    "국채": "domestic_bond",
    "기준금리": "domestic_bond",
    "채권금리": "domestic_bond",
    "달러강세": "real_assets",
    "원달러": "real_assets",
    "환율": "real_assets",
    "국제유가": "real_assets",
    "금값": "real_assets",
    "원유": "real_assets",
    "WTI": "real_assets",
}

EXPECTED_COLS = ["keyword", "title", "date"]

COLUMN_RENAME_MAP = {
    "키워드": "keyword",
    "제목": "title",
    "날짜": "date",
    "-keyword": "keyword",
    "title": "title",
    "date": "date",
}


def infer_keyword_from_filename(path: Path) -> str:
    stem = path.stem
    if not stem.startswith("mk_news_"):
        raise ValueError(f"예상한 파일명이 아님: {path.name}")
    return stem.replace("mk_news_", "", 1)


def load_one_csv(path: Path) -> pd.DataFrame:
    keyword = infer_keyword_from_filename(path)

    if keyword in EXCLUDE_KEYWORDS:
        return pd.DataFrame(columns=EXPECTED_COLS + ["section"])

    if keyword not in SECTION_MAP:
        raise ValueError(f"section 매핑이 없는 키워드 파일: {path.name}")

    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [str(col).strip() for col in df.columns]
    df = df.rename(columns=COLUMN_RENAME_MAP)

    missing_cols = [col for col in EXPECTED_COLS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"{path.name}에 필요한 컬럼이 없음: {missing_cols} / 현재 컬럼: {df.columns.tolist()}"
        )

    df = df[EXPECTED_COLS].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce", format="mixed")

    for col in ["keyword", "title"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # 키워드 컬럼은 파일명 기준으로 통일
    df["keyword"] = keyword
    df["section"] = SECTION_MAP[keyword]

    return df


def build_mk_news_geonho() -> pd.DataFrame:
    csv_paths = sorted(DATA_DIR.glob("mk_news_*.csv"))
    if not csv_paths:
        raise FileNotFoundError(f"CSV 파일을 찾지 못함: {DATA_DIR}")

    frames = []
    for path in csv_paths:
        if path.name == OUTPUT_PATH.name:
            continue
        frames.append(load_one_csv(path))

    df_all = pd.concat(frames, ignore_index=True)

    # 날짜 없는 행 제거
    df_all = df_all.dropna(subset=["date"]).reset_index(drop=True)

    # 중복 제거
    df_all = df_all.drop_duplicates(subset=["title", "date"]).reset_index(drop=True)

    # 정렬
    df_all = df_all.sort_values(["date", "section", "keyword", "title"]).reset_index(drop=True)

    return df_all


def main() -> None:
    df_final = build_mk_news_geonho()
    df_final.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"저장 완료: {OUTPUT_PATH}")
    print(f"행 개수: {len(df_final):,}")
    print("section 분포:")
    print(df_final["section"].value_counts())
    print("키워드 분포:")
    print(df_final["keyword"].value_counts())
    print(df_final.head(10))


if __name__ == "__main__":
    main()