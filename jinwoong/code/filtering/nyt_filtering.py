"""
NYT 뉴스 노이즈 제거
입력: data/raw/nyt/nyt_raw_v4.csv
출력: data/processed/nyt/nyt_final.csv

처리 순서:
  1. raw CSV 로드
  2. 키워드 내 중복 제거
  3. 노이즈 패턴 10종 제거
"""
from pathlib import Path
import pandas as pd

BASE_DIR    = Path(__file__).resolve().parent.parent.parent
INPUT_PATH  = BASE_DIR / "data/raw/nyt/nyt_raw_v4.csv"
OUTPUT_PATH = BASE_DIR / "data/processed/nyt/nyt_final.csv"

NOISE_PATTERNS = {
    "A. 스트리밍/넷플릭스 추천":  r"stream these|what\'?s on tv\b|streaming gems|leave netflix|leaving netflix|movies and shows|children\'?s movies to stream",
    "B. 부고 기사":               r"\bdies? at \d+\b|, is dead$|\bis dead,|\bhas died\b",
    "C. 웨딩 공지":               r"wedding announcement|this week\'?s wedding",
    "D. 요일별 브리핑":           r"^your (monday|tuesday|wednesday|thursday|friday|saturday|sunday|weekend)( evening)? briefing$|^(monday|tuesday|wednesday|thursday|friday|saturday|sunday) briefing$",
    "E. 책/스릴러 리뷰":          r"books we love|best thrillers|new thrillers|pulse-pounding.*thriller|book review",
    "F. 팟캐스트(금융 무관)":     r"\bpodcast\b(?!.*\b(economy|market|invest|financial|stock|trade|fed|rate|inflation)\b)",
    "G. DAX 동음이의어 인물":     r"\bdax cowart\b|\bdax shepard\b|\bdax tejera\b",
    "H. 스포츠/엔터":             r"\bsoccer\b(?!.*\b(stock|market|invest|economy)\b)|golden globe|golden globes|\bn\.f\.l\.\b|jubilant.*fans",
    "I. 생활/잡다 기사":          r"^word of the day:|^corrections: (jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|goes dog walking|holiday cards|saving room for airplane food|^celebrity moguls$|the kids are up all night",
    "J. 셀럽(금융 무관)":         r"\bprince harry\b|\bnikki glaser\b|\bparis hilton\b|\bbarbra streisand\b",
}


def main() -> None:
    df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig", dtype=str)
    df.columns = [c.strip() for c in df.columns]
    print(f"로드: {len(df):,}행")

    # 중복 제거
    df["_title_norm"] = df["title"].str.strip().str.replace(r"\s+", " ", regex=True)
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["keyword", "_title_norm"], keep="first")
    df = df.drop(columns=["_title_norm"]).reset_index(drop=True)
    print(f"중복 제거: {before_dedup - len(df):,}건 → {len(df):,}행")

    # 노이즈 패턴 제거
    titles = df["title"].fillna("").str.lower()
    noise_mask = pd.Series(False, index=df.index)
    print("\n패턴별 제거 건수:")
    for name, pat in NOISE_PATTERNS.items():
        matched = titles.str.contains(pat, regex=True, na=False)
        print(f"  {name}: {matched.sum():,}건")
        noise_mask |= matched

    df = df[~noise_mask].reset_index(drop=True)
    print(f"\n최종: {len(df):,}행")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
