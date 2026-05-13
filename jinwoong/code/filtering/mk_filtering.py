"""
MK 뉴스 노이즈 제거
입력: data/raw/mk/mk_news_[keyword]_[year].csv (개별 파일들)
출력: data/processed/mk/mk_news_final.csv

처리 순서:
  1. 개별 raw CSV 합본
  2. 카테고리 레이블 행 제거 (date NaN)
  3. 키워드 내 중복 제거
  4. 노이즈 패턴 14종 제거
"""
from pathlib import Path
import pandas as pd

BASE_DIR    = Path(__file__).resolve().parent.parent.parent
RAW_DIR     = BASE_DIR / "data/raw/mk"
OUTPUT_PATH = BASE_DIR / "data/processed/mk/mk_news_final.csv"

NOISE_PATTERNS = {
    "A. [MK포토] 스포츠 사진":       r"\[MK포토\]",
    "B. 아이넷 AI 로봇 기자 자동생성": r"\[아이넷 AI 로봇 기자\]",
    "C1. NBA/농구":                  r"\bNBA\b|르브론|웨스트브룩|아데토쿤보|웸반야마|\[NBA",
    "C2. MLB/KBO/WBC 야구":          r"류현진|배지환|오타니|다르빗슈|\[WBC\]|\[WS\d\]|WBC.*야구|MLB.*연봉|연봉.*MLB|WS 노 히터",
    "C3. 골프 LPGA/PGA":             r"LPGA|\[오태식의 골프|\[임정우의 스리|PGA투어|고진영|박성현|김효주|김세영|매킬로이",
    "C4. UFC/격투기":                 r"\bUFC\b|아데산야|뒤 플레시스",
    "C5. 축구(금융 무관)":            r"이강인.*PSG|PSG.*이강인|라우타로|풀리식|\[코파",
    "D. ELS/DLS 상품모집 광고":       r"TRUE ELS \d+회 모집|TRUE DLS \d+호 모집|부메랑스텝다운형TRUE ELS|스텝다운형TRUE ELS|스텝다운형TRUE DLS|뱅키스 전용 ELS|연 \d+\.\d+% 제공.*ELS 공모",
    "E. [코스닥 공시] 단순알림":       r"^\[코스닥 공시\]",
    "F. [美공시] 단순알림":            r"^\[美공시\]",
    "G. 대출/금리 광고":              r"DSR미적용.*금리|DSR 미적용.*금리|DSR무관.*금리|대비는.*%.*금리로|년고정 금리로!|DSR미적용·연",
    "H. 매-세-지/PICK 뉴스레터":      r"매경이 전하는 세상의 지식|\[인기 검색 종목 PICK|\[오후장 급등주 PICK",
    "I. DAX 동음이의어":              r"GS칼텍스.*DAX|사이먼 도미닉|League of Legends|Teamfight Tactics",
    "J. 연예/셀럽":                   r"이정재.*임세령|이정재 임세령",
}


def load_raw(raw_dir: Path) -> pd.DataFrame:
    files = sorted([
        f for f in raw_dir.glob("mk_news_*.csv")
        if "_all" not in f.name and "_partial" not in f.name
    ])
    frames = []
    for f in files:
        try:
            frames.append(pd.read_csv(f, dtype=str))
        except Exception as e:
            print(f"  SKIP {f.name}: {e}")
    combined = pd.concat(frames, ignore_index=True)
    print(f"합본: {len(combined):,}행 ({len(files)}개 파일)")
    return combined


def main() -> None:
    # 1. 합본
    df = load_raw(RAW_DIR)

    # 2. 카테고리 레이블 행 제거 (date NaN = 키워드명만 있는 행)
    df = df[df["date"].notna()].copy()
    print(f"레이블 행 제거 후: {len(df):,}행")

    # 3. 키워드 내 중복 제거
    df["_title_norm"] = df["title"].str.strip().str.replace(r"\s+", " ", regex=True)
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["keyword", "_title_norm"], keep="first")
    df = df.drop(columns=["_title_norm"]).reset_index(drop=True)
    print(f"중복 제거: {before_dedup - len(df):,}건 → {len(df):,}행")

    # 4. 노이즈 패턴 제거
    titles = df["title"].fillna("")
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
