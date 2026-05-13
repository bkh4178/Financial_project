#%%
from pathlib import Path
import re
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "mk_news_data"
INPUT_PATH = DATA_DIR / "mk_news_geonho.csv"
OUTPUT_PATH = DATA_DIR / "mk_news_geonho_clean.csv"


def clean_title(title: str) -> str:
    if pd.isna(title):
        return ""

    text = str(title).strip()
    if not text:
        return ""

    # 줄바꿈/탭 정리
    text = re.sub(r"[\r\n\t]+", " ", text)

    # 스마트쿼트/백틱 정리
    text = (
        text.replace("“", '"')
            .replace("”", '"')
            .replace("‘", '"')
            .replace("’", '"')
            .replace("`", '"')
    )

    # 내부의 과도한 연속 따옴표는 1개로 축소
    text = re.sub(r'"{2,}', '"', text)
    text = re.sub(r"'{2,}", "'", text)

    # 제목 양끝을 감싸는 따옴표 제거 (한 겹/여러 겹 모두)
    text = re.sub(r'^["\']+', '', text)
    text = re.sub(r'["\']+$', '', text)

    # 중간에 들어간 기획/카테고리 태그 제거
    # 예: [신년사], [국내 업종별 전망 / 자동차], [2019 경제기상도]
    text = re.sub(r'\s*\[[^\]]+\]\s*', ' ', text)

    # 유니코드 줄임표를 일반 점 3개로 통일
    text = text.replace("…", "...")

    # 공백 정리
    text = re.sub(r'\s+', ' ', text).strip()

    # 쉼표/따옴표 주변 과한 공백 정리
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\s+([,.;:])', r'\1', text)

    # 양끝 따옴표 제거 후 한 번 더 정리
    text = text.strip("\"'").strip()

    # 따옴표만 남은 경우 제거
    if text in {'"', "'"}:
        return ""

    return text


def validate_columns(df: pd.DataFrame) -> None:
    expected_cols = ["keyword", "title", "date", "section"]
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"필수 컬럼이 없음: {missing_cols} / 현재 컬럼: {df.columns.tolist()}"
        )


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"입력 파일이 없음: {INPUT_PATH}")

    df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")
    df.columns = [str(col).strip() for col in df.columns]
    validate_columns(df)

    # 날짜 타입 통일
    df["date"] = pd.to_datetime(df["date"], errors="coerce", format="mixed")

    # 제목 정제
    df["title"] = df["title"].apply(clean_title)

    # 날짜/제목 결측 제거
    df = df.dropna(subset=["date"]).reset_index(drop=True)
    df = df[df["title"].str.strip() != ""].reset_index(drop=True)

    # 정제 후 중복 다시 제거
    df = df.drop_duplicates(subset=["title", "date"]).reset_index(drop=True)

    # 정렬
    df = df.sort_values(["date", "section", "keyword", "title"]).reset_index(drop=True)

    # 저장
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"저장 완료: {OUTPUT_PATH}")
    print(f"행 개수: {len(df):,}")
    print("\nsection 분포")
    print(df["section"].value_counts())
    print("\n상위 10개 행")
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()