from pathlib import Path
import re
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
INPUT_PATH  = BASE_DIR / "data/processed/mk_news/mk_news_final.csv"
OUTPUT_PATH = BASE_DIR / "data/processed/mk_news/mk_news_preprocessed.csv"

SECTION_MAP = {
    "코스피":     "domestic_core",
    "코스닥":     "domestic_core",
    "MSCI Korea": "domestic_core",
    "S&P500":    "global_macro",
    "나스닥":     "global_macro",
    "다우존스":   "global_macro",
    "러셀":       "global_macro",
    "니케이":     "global_macro",
    "TOPIX":     "global_macro",
    "DAX":       "global_macro",
    "유로스탁스": "global_macro",
    "MSCI World": "global_macro",
    "MSCI ACWI":  "global_macro",
    "MSCI EAFE":  "global_macro",
}


def clean_title(title: str) -> str:
    if pd.isna(title):
        return ""
    text = str(title).strip()
    if not text:
        return ""

    # 줄바꿈/탭 → 공백
    text = re.sub(r"[\r\n\t]+", " ", text)

    # 스마트쿼트/백틱 통일
    text = (
        text.replace("“", '"').replace("”", '"')
            .replace("‘", '"').replace("’", '"')
            .replace("`", '"')
    )

    # 연속 따옴표 축소
    text = re.sub(r'"{2,}', '"', text)

    # 대괄호 태그 제거 ([속보], [단독], [뉴욕증시] 등 카테고리 레이블)
    text = re.sub(r'\s*\[[^\]]+\]\s*', ' ', text)

    # 유니코드 말줄임 통일
    text = text.replace("…", "...")

    # 앞뒤 따옴표 제거
    text = re.sub(r'^["\']+', '', text)
    text = re.sub(r'["\']+$', '', text)

    # 공백 정규화
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\s+([,.;:])', r'\1', text)
    text = text.strip("\"'").strip()

    if text in {'"', "'"}:
        return ""
    return text


def main() -> None:
    df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig", dtype=str)
    df.columns = [c.strip() for c in df.columns]

    # 날짜 파싱
    df["date"] = pd.to_datetime(df["date"], errors="coerce", format="mixed")
    df = df.dropna(subset=["date"]).reset_index(drop=True)

    # 제목 클리닝
    df["title"] = df["title"].apply(clean_title)
    df = df[df["title"].str.strip() != ""].reset_index(drop=True)

    # section 매핑
    df["section"] = df["keyword"].map(SECTION_MAP)
    unmapped = df[df["section"].isna()]["keyword"].unique().tolist()
    if unmapped:
        raise ValueError(f"section 매핑 안 된 keyword: {unmapped}")

    # source 추가
    df["source"] = "MK"

    # 중복 제거 (정제 후 재확인)
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
