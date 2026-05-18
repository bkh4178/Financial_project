"""
Naive Baseline: 직전 5일 수익률을 예측값으로 사용
Data: FINAL_DATA/tft_data/final_dataset_tft_ready.csv
"""

import os
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
DATA_PATH = os.path.join(ROOT, "FINAL_DATA/tft_data/final_dataset_tft_ready.csv")

TRAIN_END  = "2023-09-30"
VAL_START  = "2023-10-06"
VAL_END    = "2024-06-28"
TEST_START = "2024-07-08"

# XGBoost 결과 (비교용 고정값)
XGB_RESULTS = {
    "val":  {"MAE": 0.016564, "RMSE": 0.025075},
    "test": {"MAE": 0.020008, "RMSE": 0.031350},
}

SEP = "-" * 60


def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["target_5d"])
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)
    return df


def add_naive_pred(df: pd.DataFrame) -> pd.DataFrame:
    # ticker별 직전 5일 수익률 = lag=5 pct_change of end
    df["naive_pred"] = (
        df.groupby("ticker")["end"]
        .transform(lambda x: x.pct_change(periods=5))
    )
    return df.dropna(subset=["naive_pred"]).reset_index(drop=True)


def evaluate(y_true, y_pred, label: str) -> dict:
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = mean_squared_error(y_true, y_pred) ** 0.5
    print(f"  {label:5s} | MAE={mae:.6f}  RMSE={rmse:.6f}")
    return {"MAE": mae, "RMSE": rmse}


def main():
    print(SEP)
    print("1. 로드 & 전처리")
    print(SEP)
    df = load(DATA_PATH)
    print(f"  로드 완료: {df.shape}")

    print("\n2. Naive 예측 생성 (직전 5일 수익률)")
    df = add_naive_pred(df)
    print(f"  NaN 제거 후 shape: {df.shape}")

    print(f"\n{SEP}")
    print("3. Train/Val/Test split")
    print(SEP)
    train = df[df["date"] <= TRAIN_END]
    val   = df[(df["date"] >= VAL_START) & (df["date"] <= VAL_END)]
    test  = df[df["date"] >= TEST_START]
    for name, sub in [("train", train), ("val", val), ("test", test)]:
        print(f"  {name:5s}: {len(sub):>6,}행  "
              f"date {sub['date'].min().date()} ~ {sub['date'].max().date()}")

    print(f"\n{SEP}")
    print("4. 평가 (MAE / RMSE)")
    print(SEP)
    naive_results = {}
    naive_results["val"]  = evaluate(val["target_5d"],  val["naive_pred"],  "val")
    naive_results["test"] = evaluate(test["target_5d"], test["naive_pred"], "test")

    print(f"\n{SEP}")
    print("5. XGBoost vs Naive 비교")
    print(SEP)
    header = f"  {'모델':<12} {'구간':<6} {'MAE':>10} {'RMSE':>10}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for split_name in ("val", "test"):
        xgb = XGB_RESULTS[split_name]
        nav = naive_results[split_name]
        print(f"  {'XGBoost':<12} {split_name:<6} {xgb['MAE']:>10.6f} {xgb['RMSE']:>10.6f}")
        print(f"  {'Naive':<12} {split_name:<6} {nav['MAE']:>10.6f} {nav['RMSE']:>10.6f}")
        mae_delta  = nav["MAE"]  - xgb["MAE"]
        rmse_delta = nav["RMSE"] - xgb["RMSE"]
        sign_mae  = "+" if mae_delta  >= 0 else ""
        sign_rmse = "+" if rmse_delta >= 0 else ""
        print(f"  {'차이(N-X)':<12} {split_name:<6} {sign_mae}{mae_delta:>9.6f} {sign_rmse}{rmse_delta:>9.6f}")
        print()
    print(SEP)


if __name__ == "__main__":
    main()
