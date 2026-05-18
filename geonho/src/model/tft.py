"""
tft.py
------
TemporalFusionTransformer 인스턴스화 및 PyTorch Lightning Trainer 설정.
"""

import os
import sys

import lightning as pl
from lightning.pytorch.callbacks import EarlyStopping, ModelCheckpoint

from pytorch_forecasting import TemporalFusionTransformer
from pytorch_forecasting.metrics import MAE, RMSE, QuantileLoss
from lightning.pytorch.loggers import CSVLogger


sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config import (
    MAX_ENCODER_LENGTH,
    MAX_PREDICTION_LENGTH,
    CHECKPOINT_DIR,
    LOG_DIR,

    HIDDEN_SIZE, 
    ATTENTION_HEAD_SIZE, 
    DROPOUT, 
    HIDDEN_CONTINUOUS_SIZE, 
    LEARNING_RATE, 
    MAX_EPOCHS, 
    PATIENCE
)

QUANTILES = [0.1, 0.5, 0.9]   # 불확실성 구간 + 중앙값(point prediction)

def build_model(train_ds) -> TemporalFusionTransformer:
    """
    TimeSeriesDataSet으로부터 TFT 모델 생성.

    Parameters
    ----------
    train_ds : TimeSeriesDataSet
        dataset.py의 make_datasets()에서 반환된 train dataset.
        피처 구조(categorical embedding 크기 등)를 자동으로 추론.

    Returns
    -------
    TemporalFusionTransformer
    """
    model = TemporalFusionTransformer.from_dataset(
        train_ds,

        # ── 아키텍처 ──────────────────────────────────────────────────────────
        hidden_size=HIDDEN_SIZE,
        attention_head_size=ATTENTION_HEAD_SIZE,
        dropout=DROPOUT,
        hidden_continuous_size=HIDDEN_CONTINUOUS_SIZE,

        # ── Loss / Metrics ────────────────────────────────────────────────────
        loss=QuantileLoss(quantiles=QUANTILES),   # 학습: 분위수 손실
        logging_metrics=[MAE(), RMSE()],           # val 로깅: 베이스라인 비교용

        # ── 옵티마이저 ────────────────────────────────────────────────────────
        learning_rate=LEARNING_RATE,
        optimizer="adam",

        # ── 로깅 ──────────────────────────────────────────────────────────────
        log_interval=10,        # 10 step마다 loss 로깅
        log_val_interval=1,     # val epoch마다 로깅
    )

    return model


def build_trainer(max_epochs: int = MAX_EPOCHS) -> pl.Trainer:
    """
    PyTorch Lightning Trainer 생성.

    Callbacks
    ---------
    - EarlyStopping : val_loss 기준, patience=5
    - ModelCheckpoint : val_loss 최소 모델 저장
    """
    early_stop = EarlyStopping(
        monitor="val_loss",
        patience=PATIENCE,
        mode="min",
        verbose=True,
    )

    checkpoint = ModelCheckpoint(
        dirpath=CHECKPOINT_DIR,
        filename="tft-{epoch:02d}-{val_loss:.4f}",
        monitor="val_loss",
        mode="min",
        save_top_k=1,       # 최고 성능 1개만 저장
    )
    logger = CSVLogger(save_dir=LOG_DIR, name="")
    

    trainer = pl.Trainer(
        max_epochs=max_epochs,
        accelerator="auto",         # GPU 있으면 자동 사용, 없으면 CPU
        gradient_clip_val=0.1,      # TFT 권장 gradient clipping
        callbacks=[early_stop, checkpoint],
        logger= logger,
        enable_progress_bar=True,
    )

    return trainer


# ── sanity check ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from data.dataset import make_datasets

    train_ds, val_ds, train_loader, val_loader = make_datasets()

    model = build_model(train_ds)
    print(model)
    print(f"\n학습 파라미터 수: {sum(p.numel() for p in model.parameters()):,}")