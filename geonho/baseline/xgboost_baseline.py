"""
XGBoost Baseline + Optuna 하이퍼파라미터 튜닝
Data: FINAL_DATA/tft_data/final_dataset_tft_ready.csv
"""

import os
import warnings
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error
import xgboost as xgb
import optuna
from optuna.samplers import TPESampler

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)  # trial별 로그 억제

N_TRIALS = 50

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
DATA_PATH = os.path.join(ROOT, "FINAL_DATA/tft_data/final_dataset_tft_ready.csv")

TRAIN_END  = "2023-09-30"
VAL_START  = "2023-10-06"
VAL_END    = "2024-06-30"
TEST_START = "2024-07-06"

SEP = "-" * 60


# ── 1. 로드 & 전처리 ──────────────────────────────────────────────
def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["target_5d"]).reset_index(drop=True)
    df = df.drop(columns=["name", "time_idx"])
    return df


# ── 2. Rolling 피처 생성 (ticker별) ──────────────────────────────
def add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    def _roll(g):
        g = g.sort_values("date")
        ret = g["end"].pct_change()
        g["end_ma5"]   = g["end"].rolling(5).mean()
        g["end_ma20"]  = g["end"].rolling(20).mean()
        g["end_vol5"]  = ret.rolling(5).std()
        g["end_vol20"] = ret.rolling(20).std()
        return g

    df = df.groupby("ticker", group_keys=False).apply(_roll)
    return df.dropna().reset_index(drop=True)


# ── 3. Label Encoding ─────────────────────────────────────────────
def label_encode(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["ticker", "sector"]:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
    return df


# ── 4. Train/Val/Test split ───────────────────────────────────────
def split(df: pd.DataFrame):
    train = df[df["date"] <= TRAIN_END]
    val   = df[(df["date"] >= VAL_START) & (df["date"] <= VAL_END)]
    test  = df[df["date"] >= TEST_START]

    for name, sub in [("train", train), ("val", val), ("test", test)]:
        print(f"  {name:5s}: {len(sub):>6,}행  "
              f"date {sub['date'].min().date()} ~ {sub['date'].max().date()}")

    feature_cols = [c for c in df.columns if c not in ("target_5d", "date")]

    def xy(sub):
        return sub[feature_cols].values, sub["target_5d"].values

    return xy(train), xy(val), xy(test), feature_cols


# ── 5. Optuna 튜닝 ───────────────────────────────────────────────
def tune(X_train, y_train, X_val, y_val) -> dict:
    def objective(trial: optuna.Trial) -> float:
        params = {
            "n_estimators":     500,
            "learning_rate":    trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "max_depth":        trial.suggest_int("max_depth", 3, 4),
            "subsample":        trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 20),
            "random_state":     42,
            "n_jobs":           -1,
            "tree_method":      "hist",
        }
        model = xgb.XGBRegressor(**params)
        model.fit(X_train, y_train, verbose=False)
        pred = model.predict(X_val)
        return mean_squared_error(y_val, pred) ** 0.5

    study = optuna.create_study(direction="minimize", sampler=TPESampler(seed=42))
    study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=True)

    print(f"\n  Best val RMSE : {study.best_value:.6f}")
    print(f"  Best params   :")
    for k, v in study.best_params.items():
        print(f"    {k:<22s} = {v}")

    return study.best_params


# ── 6. 평가 ──────────────────────────────────────────────────────
def evaluate(model, X, y, label: str):
    pred = model.predict(X)
    mae  = mean_absolute_error(y, pred)
    rmse = mean_squared_error(y, pred) ** 0.5
    print(f"  {label:5s} | MAE={mae:.6f}  RMSE={rmse:.6f}")


# ── main ──────────────────────────────────────────────────────────
def main():
    print(SEP)
    print("1. 로드 & 전처리")
    print(SEP)
    df = load(DATA_PATH)
    print(f"  로드 완료: {df.shape}")

    print("\n2. Rolling 피처 생성")
    df = add_rolling_features(df)
    print(f"  Rolling 후 shape: {df.shape}")

    print("\n3. Label Encoding (ticker, sector)")
    df = label_encode(df)

    print(f"\n{SEP}")
    print("4. Train/Val/Test split")
    print(SEP)
    (X_train, y_train), (X_val, y_val), (X_test, y_test), feature_cols = split(df)

    print(f"\n{SEP}")
    print(f"5. Optuna 하이퍼파라미터 튜닝 (n_trials={N_TRIALS})")
    print(SEP)
    best_params = tune(X_train, y_train, X_val, y_val)

    print(f"\n{SEP}")
    print("6. 최적 파라미터로 최종 모델 학습")
    print(SEP)
    final_model = xgb.XGBRegressor(
        n_estimators=500,
        random_state=42,
        n_jobs=-1,
        tree_method="hist",
        **best_params,
    )
    final_model.fit(X_train, y_train, verbose=100)

    print(f"\n{SEP}")
    print("7. Feature Importance (상위 15개)")
    print(SEP)
    importance = pd.Series(final_model.feature_importances_, index=feature_cols)
    for feat, score in importance.sort_values(ascending=False).head(15).items():
        print(f"  {feat:<25s} {score:.4f}")

    print(f"\n{SEP}")
    print("8. 최종 평가 (MAE / RMSE)")
    print(SEP)
    evaluate(final_model, X_train, y_train, "train")
    evaluate(final_model, X_val,   y_val,   "val")
    evaluate(final_model, X_test,  y_test,  "test")
    print(SEP)


if __name__ == "__main__":
    main()
