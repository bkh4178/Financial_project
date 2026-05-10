"""
FINAL_DATA/FINAL/final_dataset_for_tft_*.csv 파일들을 병합하여
FINAL_DATA/final_dataset_all.csv 로 저장합니다.

macro 컬럼(usd_krw, vix_close)이 개별 파일에 포함된 경우 따로 추출해
date 기준으로 병합한 뒤 최종 데이터에 left join합니다.
"""

import glob
import os
import pandas as pd

FINAL_DIR = os.path.join(os.path.dirname(__file__), "FINAL")
OUTPUT_PATH     = os.path.join(os.path.dirname(__file__), "final_dataset_all.csv")
OUTPUT_PATH_FILLED = os.path.join(os.path.dirname(__file__), "final_dataset_all_filled.csv")

REQUIRED_COLUMNS = [
    "date", "ticker", "name", "end", "AUM", "target_5d", "sector",
    "domestic_mean", "domestic_std", "domestic_count",
    "global_mean", "global_std", "global_count",
]

# 각 macro 컬럼을 가져올 파일명을 명시적으로 지정
MACRO_SOURCE = {
    "usd_krw":   "final_dataset_for_tft_final.csv",
    "vix_close":  "final_dataset_for_tft_jw.csv",
}
MACRO_COLUMNS = list(MACRO_SOURCE.keys())

SENTIMENT_COLUMNS = [
    "domestic_mean", "domestic_std", "domestic_count",
    "global_mean", "global_std", "global_count",
]

SEP = "-" * 60


def validate_file(path: str) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """검증된 (main_df, macro_df) 튜플 반환. macro 컬럼이 없으면 macro_df=None."""
    filename = os.path.basename(path)
    print(f"\n{'=' * 60}")
    print(f"[파일] {filename}")

    # BOM 포함 여부에 관계없이 읽기
    df = pd.read_csv(path, encoding="utf-8-sig")

    # ── 0. macro 컬럼 분리 ────────────────────────────────────
    # MACRO_SOURCE에 지정된 파일에서만 해당 컬럼 추출
    found_macro = [
        c for c in MACRO_COLUMNS
        if c in df.columns and MACRO_SOURCE.get(c) == filename
    ]
    macro_df: pd.DataFrame | None = None
    if found_macro:
        print(f"  [INFO] macro 컬럼 감지 → 분리: {found_macro}")
        macro_df = df[["date"] + found_macro].copy()
        macro_df["date"] = pd.to_datetime(macro_df["date"], errors="coerce")
        macro_df = macro_df.dropna(subset=["date"]).drop_duplicates(subset=["date"])
    elif any(c in df.columns for c in MACRO_COLUMNS):
        skipped = [c for c in MACRO_COLUMNS if c in df.columns]
        print(f"  [INFO] macro 컬럼 {skipped} 존재하나 지정 소스 아님 → 무시")

    # ── 1. 컬럼 검증 ──────────────────────────────────────────
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    extra   = [c for c in df.columns if c not in REQUIRED_COLUMNS + MACRO_COLUMNS]
    if missing:
        print(f"  [FAIL] 누락 컬럼: {missing}")
        return None, macro_df
    if extra:
        print(f"  [WARN] 추가 컬럼 (무시): {extra}")
    print(f"  [OK]   컬럼 일치")

    # 기준 컬럼 순서로 정렬 (macro 컬럼 제외)
    df = df[REQUIRED_COLUMNS]

    # ── 2. date dtype 검증 ────────────────────────────────────
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    nat_count = df["date"].isna().sum()
    if nat_count > 0:
        print(f"  [FAIL] date 변환 실패 행: {nat_count}개")
        return None, macro_df
    print(f"  [OK]   date dtype → {df['date'].dtype}")

    # ── 3. sector 유니크 값 ───────────────────────────────────
    sectors = sorted(df["sector"].dropna().unique().tolist())
    print(f"  [INFO] sector 유니크: {sectors}")

    # ── 4. ticker 유니크 값 ───────────────────────────────────
    tickers = sorted(df["ticker"].astype(str).unique().tolist())
    print(f"  [INFO] ticker 유니크 ({len(tickers)}개): {tickers}")

    print(f"  [OK]   검증 통과  shape={df.shape}")
    return df, macro_df


def consolidate_macro(macro_frames: list[pd.DataFrame]) -> pd.DataFrame | None:
    """여러 파일에서 추출한 macro_df들을 date 기준으로 병합."""
    if not macro_frames:
        return None

    combined = macro_frames[0]
    for other in macro_frames[1:]:
        new_cols = [c for c in other.columns if c not in combined.columns]
        overlap_cols = [c for c in other.columns if c != "date" and c in combined.columns]

        # 겹치는 macro 컬럼 값 충돌 여부 확인
        if overlap_cols:
            check = combined.merge(other, on="date", suffixes=("_a", "_b"), how="inner")
            for col in overlap_cols:
                diff = (check[f"{col}_a"] - check[f"{col}_b"]).abs()
                if diff.max() > 1e-6:
                    print(f"  [WARN] macro 컬럼 '{col}' 값 충돌 감지 — 첫 번째 파일 값 우선 사용")

        # 새 컬럼만 병합, 기존 컬럼은 첫 파일 값 유지
        if new_cols:
            combined = combined.merge(other[["date"] + new_cols], on="date", how="outer")

    combined = combined.sort_values("date").reset_index(drop=True)
    return combined


def main() -> None:
    # ── 파일 목록 자동 감지 ───────────────────────────────────
    pattern = os.path.join(FINAL_DIR, "final_dataset_for_tft_*.csv")
    paths = sorted(glob.glob(pattern))

    # .csv.csv 처럼 이중 확장자 파일도 *.csv 패턴에 포함되지만
    # 중복 감지를 위해 deduplicate (동일 경로가 두 번 잡히는 경우 방지)
    paths = list(dict.fromkeys(paths))

    if not paths:
        print(f"[ERROR] 파일을 찾을 수 없습니다: {pattern}")
        return

    print(f"감지된 파일 {len(paths)}개:")
    for p in paths:
        print(f"  {os.path.basename(p)}")

    # ── 각 파일 검증 및 로드 ──────────────────────────────────
    frames: list[pd.DataFrame] = []
    macro_frames: list[pd.DataFrame] = []
    for p in paths:
        df, macro_df = validate_file(p)
        if df is not None:
            frames.append(df)
        if macro_df is not None:
            macro_frames.append(macro_df)

    print(f"\n{SEP}")
    print(f"검증 통과: {len(frames)}/{len(paths)}개 파일")

    if not frames:
        print("[ERROR] 병합할 파일이 없습니다.")
        return

    # ── concat ────────────────────────────────────────────────
    merged = pd.concat(frames, ignore_index=True)

    # ── ticker 중복 행 경고 ───────────────────────────────────
    dup_mask = merged.duplicated(subset=["date", "ticker"], keep=False)
    dup_count = dup_mask.sum()
    if dup_count > 0:
        print(f"\n[WARN] (date, ticker) 중복 행 {dup_count}개 감지:")
        print(merged[dup_mask][["date", "ticker", "sector"]].sort_values(["date", "ticker"]).to_string(index=False))
    else:
        print("\n[OK]   (date, ticker) 중복 없음")

    # ── macro 컬럼 date 기준 병합 ─────────────────────────────
    macro_combined = consolidate_macro(macro_frames)
    if macro_combined is not None:
        macro_cols = [c for c in macro_combined.columns if c != "date"]
        print(f"\n[INFO] macro 컬럼 병합: {macro_cols}")
        print(f"       macro date 범위: {macro_combined['date'].min().date()} ~ {macro_combined['date'].max().date()}")
        merged = merged.merge(macro_combined, on="date", how="left")
        for col in macro_cols:
            na_count = merged[col].isna().sum()
            if na_count > 0:
                print(f"  [WARN] '{col}' NaN {na_count}행 (date 불일치)")
        print(f"  [OK]   macro 병합 완료  shape={merged.shape}")
    else:
        print("\n[INFO] macro 컬럼 없음 — 그대로 진행")

    # ── date 오름차순 정렬 후 저장 (원본) ────────────────────
    merged = merged.sort_values("date").reset_index(drop=True)
    merged.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\n[저장] 원본: {OUTPUT_PATH}")

    # ── sentiment 결측치 0 처리 후 저장 ──────────────────────
    fill_cols = [c for c in SENTIMENT_COLUMNS if c in merged.columns]
    merged_filled = merged.copy()
    merged_filled[fill_cols] = merged_filled[fill_cols].fillna(0)
    na_before = merged[fill_cols].isna().sum().sum()
    print(f"  [INFO] sentiment 결측치 {na_before}개 → 0으로 대체")
    merged_filled.to_csv(OUTPUT_PATH_FILLED, index=False, encoding="utf-8-sig")
    print(f"[저장] 결측치 처리: {OUTPUT_PATH_FILLED}")

    # ── 최종 요약 출력 ────────────────────────────────────────
    print(f"\n{SEP}")
    print(f"최종 shape    : {merged.shape}")
    print(f"date 범위     : {merged['date'].min().date()} ~ {merged['date'].max().date()}")

    sector_ticker = (
        merged.groupby("sector")["ticker"]
        .nunique()
        .sort_values(ascending=False)
        .rename("ticker_수")
    )
    print(f"\n섹터별 ticker 수:\n{sector_ticker.to_string()}")
    print(SEP)


if __name__ == "__main__":
    main()
