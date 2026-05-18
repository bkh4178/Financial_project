"""
config.py
---------
프로젝트 전역 상수. preprocess.py / dataset.py / train.py 모두 여기서 import.

디렉토리 구조:
    Financial_project/
    ├── FINAL_DATA/
    │   └── tft_data/
    │       └── final_dataset_tft_ready.csv   ← 원본 데이터
    └── geonho/
        └── src/
            ├── config.py
            ├── train.py
            ├── predict.py
            ├── data/
            │   ├── preprocess.py
            │   └── dataset.py
            ├── model/
            │   └── tft.py
            └── outputs/
                ├── checkpoints/
                ├── logs/
                ├── scalers/
                └── data/
                    └── final_dataset_preprocessed.csv
"""

import os

# ── 기준 경로 ──────────────────────────────────────────────────────────────────
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))       # src/
_ROOT_DIR = os.path.join(_SRC_DIR, "../..")        # Financial_project/
_OUT_DIR = os.path.join(_SRC_DIR, "outputs")                # src/outputs/

# ── 데이터 경로 ────────────────────────────────────────────────────────────────
RAW_DATA_PATH       = os.path.join(_ROOT_DIR, "FINAL_DATA", "tft_data", "final_dataset_tft_ready.csv")
PROCESSED_DATA_PATH = os.path.join(_OUT_DIR, "data", "final_dataset_preprocessed.csv")
SCALER_DIR          = os.path.join(_OUT_DIR, "scalers")
CHECKPOINT_DIR      = os.path.join(_OUT_DIR, "checkpoints")
LOG_DIR             = os.path.join(_OUT_DIR, "logs")

# ── Train/Val Split ────────────────────────────────────────────────────────────
# target_5d(t) = log(end_{t+5} / end_t) 이므로 train 마지막 row의 target이
# validation 구간 가격을 참조하지 않도록 TRAIN_END_DATE와 VAL_START_DATE를 분리.
#
# TRAIN_END_DATE = "2024-07-23"  → train feature row 마지막 날짜
# VAL_START_DATE = "2024-07-30"  → validation prediction 시작 날짜
#
# 본 모델은 t일 장 마감 이후 관측 가능한 가격, AUM, 뉴스 감성, 매크로 변수를
# 이용하여 t+5 거래일 누적 로그수익률을 예측한다.
# → preprocess.py, dataset.py 모두 이 두 날짜만 참조할 것

TRAIN_END_DATE = "2024-07-23"   # train feature row 마지막 날짜
VAL_START_DATE = "2024-07-30"   # validation prediction 시작 날짜

# ── 컬럼 정의 ──────────────────────────────────────────────────────────────────
TARGET_COL   = "target_5d"
GROUP_COL    = "ticker"
SECTOR_COL   = "sector"
TIME_IDX_COL = "time_idx"

# log1p 변환 대상 (원본 컬럼명)
LOG1P_COLS = ["AUM", "domestic_count", "global_count"]

# sector별 z-score 대상 (log1p 변환 후 컬럼명 포함)
SECTOR_ZSCORE_COLS = [
    "domestic_mean",
    "domestic_std",
    "domestic_count_log",
    "global_mean",
    "global_std",
    "global_count_log",
]

# 전체 StandardScaler 대상 (모든 ticker 공통 macro 변수)
MACRO_SCALE_COLS = ["usd_krw", "vix_close"]

# TimeSeriesDataSet time-varying unknown reals (전처리 완료 기준 컬럼명)
TIME_VARYING_UNKNOWN_REALS = [
    "end",
    "AUM_log",
    "domestic_mean",
    "domestic_std",
    "domestic_count_log",
    "global_mean",
    "global_std",
    "global_count_log",
    "usd_krw",
    "vix_close",
]


# ── 모델 하이퍼파라미터 (수정)────────────────────────────────────────────────────────
MAX_ENCODER_LENGTH    = 60
MAX_PREDICTION_LENGTH = 1
BATCH_SIZE            = 64
LEARNING_RATE         = 3e-4

# ── TFT 아키텍처 ──────────────────────────────────────────────────────────────
HIDDEN_SIZE            = 32
ATTENTION_HEAD_SIZE    = 2
DROPOUT                = 0.1
HIDDEN_CONTINUOUS_SIZE = 16

# ── Trainer ───────────────────────────────────────────────────────────────────
MAX_EPOCHS = 50
PATIENCE   = 5