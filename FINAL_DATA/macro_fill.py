"""
final_dataset_all.csv 의 macro 컬럼(usd_krw, vix_close)을
날짜 수준에서 ffill(limit=3) 처리 후 저장합니다.

출력: final_dataset_all_macro_filled.csv
"""

import os
import pandas as pd

FINAL_DATA_DIR = os.path.dirname(__file__)
TFT_DIR = os.path.join(FINAL_DATA_DIR, "tft_data")
INPUT_PATH  = os.path.join(TFT_DIR, "final_dataset_all_filled.csv")
OUTPUT_PATH = os.path.join(TFT_DIR, "final_dataset_all_macro_filled.csv")

MACRO_COLUMNS = ["usd_krw", "vix_close"]

SEP = "-" * 60


def main() -> None:
    if not os.path.exists(INPUT_PATH):
        print(f"[ERROR] 입력 파일 없음: {INPUT_PATH}")
        print("        merge_final.py를 먼저 실행하세요. (final_dataset_all_filled.csv)")
        return

    df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    target_cols = [c for c in MACRO_COLUMNS if c in df.columns]
    if not target_cols:
        print("[ERROR] 처리할 macro 컬럼이 없습니다.")
        return

    # 날짜 수준으로 추출 → ffill(limit=3) → 패널에 재병합
    macro_date = (
        df[["date"] + target_cols]
        .drop_duplicates(subset=["date"])
        .sort_values("date")
        .reset_index(drop=True)
    )
    macro_date[target_cols] = macro_date[target_cols].ffill(limit=5)

    df = df.drop(columns=target_cols)
    df = df.merge(macro_date, on="date", how="left")
    df = df.sort_values("date").reset_index(drop=True)

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"[저장] {OUTPUT_PATH}")

    # 잔여 결측 확인
    print(f"\n[ 잔여 결측 확인 ]")
    print(SEP)
    for col in target_cols:
        na_count = df[col].isna().sum()
        status = "OK" if na_count == 0 else "WARN"
        print(f"  [{status}] {col}: NaN {na_count}행")


if __name__ == "__main__":
    main()
