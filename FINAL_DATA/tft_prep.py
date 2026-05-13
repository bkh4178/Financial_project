"""
final_dataset_all_macro_filled.csv → final_dataset_tft_ready.csv

수행 작업:
  1. date 컬럼 → datetime64
  2. ticker / date 기준 오름차순 정렬
  3. ticker별 time_idx 추가 (groupby cumcount)
  4. 한글 sector명 → 영문 매핑
  5. 검증 출력 후 저장
"""

import os
import pandas as pd

FINAL_DATA_DIR = os.path.dirname(__file__)
TFT_DIR    = os.path.join(FINAL_DATA_DIR, "tft_data")
INPUT_PATH  = os.path.join(TFT_DIR, "final_dataset_all_macro_filled.csv")
OUTPUT_PATH = os.path.join(TFT_DIR, "final_dataset_tft_ready.csv")

SECTOR_MAP = {
    "가치배당":   "defensive",
    "단기자금":   "rate_cash",
    "반도체":    "Semiconductor",
    "중국 증시":  "ChinaEquity",
    "2차전지":   "SecondaryBattery",
    "빅테크":    "BigTech",
    "인도 증시":  "IndiaEquity",
}

SEP = "-" * 60


def main() -> None:
    if not os.path.exists(INPUT_PATH):
        print(f"[ERROR] 입력 파일 없음: {INPUT_PATH}")
        print("        macro_fill.py를 먼저 실행하세요.")
        return

    df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")

    # 1. date → datetime64
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    nat_count = df["date"].isna().sum()
    if nat_count > 0:
        print(f"[WARN] date 변환 실패 행 {nat_count}개 — 제거합니다.")
        df = df.dropna(subset=["date"])

    # 2. ticker / date 오름차순 정렬
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

    # 3. ticker별 time_idx
    df["time_idx"] = df.groupby("ticker").cumcount()

    # 4. sector 한글 → 영문
    before = df["sector"].unique().tolist()
    df["sector"] = df["sector"].replace(SECTOR_MAP)
    after = df["sector"].unique().tolist()
    unmapped = [s for s in after if any(ord(c) > 127 for c in str(s))]
    print(f"[INFO] sector 매핑 전: {sorted(before)}")
    print(f"[INFO] sector 매핑 후: {sorted(after)}")
    if unmapped:
        print(f"[WARN] 아직 한글이 남아있는 sector값: {unmapped}")
    else:
        print("[OK]   sector 한글 → 영문 변환 완료")

    # 5. 검증
    print(f"\n{SEP}")
    print(f"전체 shape     : {df.shape}")
    print(f"time_idx 범위  : {df['time_idx'].min()} ~ {df['time_idx'].max()}")

    starts = df.groupby("ticker")["time_idx"].min()
    bad = starts[starts != 0]
    if bad.empty:
        print("[OK]   모든 ticker time_idx 0에서 시작")
    else:
        print(f"[WARN] time_idx가 0으로 시작하지 않는 ticker: {bad.to_dict()}")

    lengths = df.groupby("ticker")["time_idx"].max() + 1
    print(f"\nticker별 time_idx 길이:")
    print(lengths.to_string())
    print(f"\n  min={lengths.min()}, max={lengths.max()}, mean={lengths.mean():.1f}")
    print(SEP)

    # 저장
    os.makedirs(TFT_DIR, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\n[저장] {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
