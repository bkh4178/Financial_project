"""
usd_krw, vix_close 결측 날짜 확인
- 소스 파일에서 각 컬럼의 결측 날짜 출력
- 병합 결과(final_dataset_all.csv)가 있으면 거기서도 추가 확인
"""

import os
import pandas as pd

FINAL_DIR  = os.path.join(os.path.dirname(__file__), "FINAL")
MERGED_PATH = os.path.join(os.path.dirname(__file__), "final_dataset_all.csv")

MACRO_SOURCE = {
    "usd_krw":  os.path.join(FINAL_DIR, "final_dataset_for_tft_final.csv"),
    "vix_close": os.path.join(FINAL_DIR, "final_dataset_for_tft_jw.csv"),
}

SEP = "-" * 60


def check_source_files() -> None:
    print("[ 소스 파일 결측 확인 ]")
    print(SEP)
    for col, path in MACRO_SOURCE.items():
        filename = os.path.basename(path)
        print(f"\n▶ {col}  ←  {filename}")
        if not os.path.exists(path):
            print(f"  [ERROR] 파일 없음: {path}")
            continue

        df = pd.read_csv(path, encoding="utf-8-sig", usecols=["date", col])
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.drop_duplicates(subset=["date"]).sort_values("date")

        na_dates = df.loc[df[col].isna(), "date"].dt.date.tolist()
        total = len(df)
        if na_dates:
            print(f"  결측 {len(na_dates)}건 / 전체 {total}행:")
            for d in na_dates:
                print(f"    {d}")
        else:
            print(f"  결측 없음  (전체 {total}행)")


def check_merged_file() -> None:
    print(f"\n\n[ 병합 결과 결측 확인 ]  {os.path.basename(MERGED_PATH)}")
    print(SEP)
    if not os.path.exists(MERGED_PATH):
        print("  병합 파일 없음 — merge_final.py를 먼저 실행하세요.")
        return

    df = pd.read_csv(MERGED_PATH, encoding="utf-8-sig")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    for col in MACRO_SOURCE:
        if col not in df.columns:
            print(f"\n▶ {col}: 컬럼 없음")
            continue

        na_dates = (
            df.loc[df[col].isna(), "date"]
            .drop_duplicates()
            .sort_values()
            .dt.date
            .tolist()
        )
        print(f"\n▶ {col}")
        if na_dates:
            print(f"  결측 date {len(na_dates)}개:")
            for d in na_dates:
                print(f"    {d}")
        else:
            print(f"  결측 없음")


if __name__ == "__main__":
    check_source_files()
    check_merged_file()
