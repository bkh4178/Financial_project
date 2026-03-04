# WandB를 이용한 AI/ML 협업 가이드

이 문서는 머신러닝 프로젝트의 실험 과정을 체계적으로 관리하고, 팀원들과 효율적으로 협업하기 위해 **WandB(Weights & Biases)**를 사용하는 방법을 안내합니다.

---

## ## 목차

1.  [WandB란 무엇인가?](#1-wandb란-무엇인가)
2.  [왜 WandB를 사용해야 하는가?](#2-왜-wandb를-사용해야-하는가)
3.  [WandB를 이용한 협업 워크플로우](#3-wandb를-이용한-협업-워크플로우)
4.  [간단 실습 코드](#4--간단-실습-코드)

---

## 1. WandB란 무엇인가?

**WandB (Weights & Biases)**는 머신러닝 개발자를 위한 **MLOps(Machine Learning Operations) 플랫폼**입니다. 복잡한 AI/ML 모델의 학습 과정을 쉽게 추적하고, 시각화하며, 재현할 수 있도록 도와주는 도구입니다. 간단히 말해 **"AI/ML 실험을 위한 GitHub"**라고 생각할 수 있습니다.

실험마다 달라지는 하이퍼파라미터, 모델 성능 지표(metric), 학습 환경, 심지어 예측 결과물까지 모든 것을 기록하고 중앙 대시보드에서 관리할 수 있습니다.

### 유사한 도구들

* **TensorBoard**: TensorFlow에서 시작된 시각화 도구로, 로컬 환경에서 실험 결과를 확인할 때 주로 사용됩니다.
* **MLflow**: 모델의 전체 생명주기 관리를 목표로 하는 오픈소스 플랫폼으로, 실험 추적, 모델 패키징, 배포 등 다양한 기능을 제공합니다.
* **Neptune.ai**: WandB와 유사한 상용 MLOps 플랫폼으로, 실험 추적 및 모델 레지스트리 기능을 중심으로 합니다.

---

## 2. 왜 WandB를 사용해야 하는가?

다양한 도구 중에서도 WandB는 특히 팀 협업과 사용 편의성 측면에서 다음과 같은 강력한 이점을 가집니다.

* **📊 강력하고 직관적인 시각화**: 수백 개의 실험 결과를 단 몇 번의 클릭만으로 비교하고 분석할 수 있는 미려하고 인터랙티브한 대시보드를 제공합니다. 누가 어떤 하이퍼파라미터로 실험했는지, 각 실험의 성능은 어땠는지 한눈에 파악할 수 있습니다.

* **⚙️ 최소한의 코드로 자동 로깅**: 기존 학습 코드에 단 몇 줄만 추가하면 하이퍼파라미터, 성능 지표뿐만 아니라 GPU 사용량, 학습 코드의 Git commit hash까지 알아서 기록해 줍니다. 실험 관리를 위한 부가적인 코드를 짤 필요가 거의 없습니다.

* **🤝 협업을 위한 중앙 허브**: 모든 팀원의 실험 결과가 하나의 **중앙 대시보드(Project)**에 자동으로 취합됩니다. 더 이상 슬랙이나 카톡으로 스크린샷을 공유하거나, 엑셀 시트에 수동으로 결과를 정리할 필요가 없습니다.

* **📝 실험 과정과 결과의 문서화 (Reports)**: WandB의 **리포트(Report)** 기능을 사용하면, 대시보드의 특정 그래프와 분석 내용을 가져와 글로 정리할 수 있습니다. 이를 통해 실험의 발견점이나 결론을 팀 전체에 공유하는 기술 문서(Live Document)를 만들 수 있습니다.

---

## 3. WandB를 이용한 협업 워크플로우

WandB의 핵심 기능들을 활용하여 팀의 협업 효율과 실험의 재현성을 극대화하는 워크플로우입니다.

#### **1단계: `wandb.init()` - 실험의 시작과 설정**

모든 WandB 작업은 실험을 초기화하는 `wandb.init()`으로 시작됩니다. 이 단계에서 실험의 기본 정보를 명확히 정의하는 것이 협업의 첫걸음입니다.

* **`project` & `entity`**: `entity`에는 **팀 이름**을, `project`에는 **공유할 작업 이름**을 지정하여 모든 팀원의 실험을 하나의 대시보드에 모읍니다.
* **`config`**: 실험에 사용될 모든 **하이퍼파라미터** (learning rate, batch size, model architecture 등)를 딕셔너리 형태로 저장합니다. 이렇게 저장된 `config`는 대시보드에서 각 실험을 그룹화하고 비교하는 강력한 기준이 됩니다.
* **`name`**: 각 실험(`Run`)에 `lr_0.01-bs_32`와 같이 고유하고 식별하기 쉬운 이름을 붙여주면 대시보드에서 특정 실험을 찾기 용이합니다.
* **`notes`**: 해당 실험에 대한 간단한 메모나 가설을 기록할 수 있습니다.

#### **2단계: `wandb.log()` - 학습 과정의 모든 것 추적하기**

`wandb.log()`는 단순히 loss, accuracy 같은 스칼라 값만 기록하는 함수가 아닙니다. 거의 모든 종류의 데이터를 기록하여 학습 과정을 입체적으로 분석할 수 있게 해줍니다.

* **기본 지표 (Metrics)**: `wandb.log({"loss": 0.1, "accuracy": 0.95})`와 같이 딕셔너리 형태로 전달하면, 시간에 따른 변화를 꺾은선 그래프로 그려줍니다.

* **표 데이터 (`wandb.Table`)**: 모델의 예측 결과를 상세하게 분석하고 싶을 때 사용합니다. epoch마다 혹은 학습이 끝난 후, 모델이 어떤 예측을 했고 정답은 무엇이었는지 표로 만들어 기록할 수 있습니다.
    ```python
    # Validation 결과를 담을 테이블 생성
    table = wandb.Table(columns=["Image", "Prediction", "Ground Truth"])
    for img, pred, truth in validation_results:
        table.add_data(wandb.Image(img), pred, truth)
    wandb.log({"validation_table": table})
    ```

* **이미지 및 시각화 (`wandb.Image`, `matplotlib`)**: 모델의 예측 결과 이미지, Confusion Matrix, Attention Map 등 시각적인 결과물을 직접 대시보드에 기록할 수 있습니다. Matplotlib으로 생성한 그래프(figure) 객체를 그대로 `wandb.log()`에 전달하면 이미지로 변환하여 저장해 줍니다.
    ```python
    # Matplotlib으로 Confusion Matrix 생성
    fig, ax = plt.subplots()
    # ... (그래프 그리는 코드) ...
    wandb.log({"confusion_matrix": fig})
    ```

#### **3단계: 재현성 확보 - 코드, 모델, 데이터셋 버전 관리**

"제 컴퓨터에서는 잘 됐는데요?" 라는 말을 없애기 위해, 실험 환경을 그대로 복제할 수 있도록 모든 소스를 버전 관리하고 저장합니다.

* **`wandb.save()` (단순 파일 저장)**: `model.h5`와 같은 모델 체크포인트나 `config.yaml` 같은 설정 파일을 해당 `Run`에 종속시켜 저장하는 간단한 방법입니다. 하지만 버전 관리 기능은 없습니다.

* **`wandb.Artifacts` (강력한 버전 관리 시스템)**: **Artifacts**는 데이터셋, 모델, 코드 등 실험의 모든 구성 요소를 버전 관리하는 가장 강력하고 권장되는 방법입니다.
    * **소스 코드 저장**: 실험에 사용된 스크립트나 전체 소스코드 폴더를 Artifact로 만들어 저장하면, 어떤 코드로 이 결과가 나왔는지 100% 보장할 수 있습니다.
    * **모델 가중치 저장**: 학습이 완료된 모델 파일을 Artifact로 저장하면, `v1`, `v2` 와 같이 버전을 붙여 관리할 수 있습니다. 다른 팀원은 이 Artifact를 내려받아 추론이나 추가 학습에 사용할 수 있습니다.
    * **데이터셋 저장**: 특정 전처리를 거친 `train_v1.csv`와 같은 데이터셋을 Artifact로 저장하여, 모든 팀원이 동일한 버전의 데이터로 실험을 진행하도록 보장할 수 있습니다.

    ```python
    # 1. Artifact 객체 생성
    artifact = wandb.Artifact('my-awesome-model', type='model')
    # 2. 파일 추가
    artifact.add_file('model.h5')
    # 3. Artifact를 Run에 기록 (로깅)
    run.log_artifact(artifact)
    ```

#### **4단계: `wandb.finish()` - 실험 종료 및 동기화**

실험이 모두 끝나면 `run.finish()`를 호출하여 해당 `Run`을 종료하고, 로컬에 남아있을 수 있는 모든 데이터를 WandB 서버와 동기화합니다. (스크립트가 정상 종료되면 자동으로 호출됩니다.)

---

## 4. 간단 실습 코드

아래 코드는 가상의 데이터와 모델로 위에서 설명한 주요 기능들(Table, Image, Artifacts)을 모두 사용하는 예제입니다.

#### **1. 라이브러리 설치**

실습에 필요한 라이브러리들을 먼저 설치합니다.

```bash
pip install wandb numpy matplotlib scikit-learn
wandb login
```

#### **2. Python 스크립트 예제 (`wandb_practice.py`)**

```python
import wandb
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import random

# --- 1. 실험 초기화 ---
run = wandb.init(
    project="practice",
    entity="capstone-algo",
    name="kijeong-practice",
    config={
        "learning_rate": 0.005,
        "epochs": 20,
        "batch_size": 128,
        "architecture": "SimpleNN",
        "dataset": "scikit-learn-dummy",
    }
)
config = wandb.config

# --- 2. 가상 데이터셋 및 모델 준비 ---
# 재현성을 위해 random seed 고정
np.random.seed(42)
random.seed(42)

# 가상 데이터 생성
X, y = make_classification(n_samples=1000, n_features=20, n_informative=2, n_redundant=10, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# --- 3. 가상 학습 루프 ---
print("Starting training...")
for epoch in range(config.epochs):
    loss = 1.0 / (epoch + 1) + random.uniform(-0.1, 0.1)
    accuracy = 1 - loss + random.uniform(-0.05, 0.05)
    
    # 기본 지표 로깅
    wandb.log({"epoch": epoch, "loss": loss, "accuracy": accuracy})
    print(f"Epoch {epoch+1}: Loss={loss:.4f}, Accuracy={accuracy:.4f}")

# --- 4. 최종 평가 및 시각화 로깅 ---
print("Logging visualizations...")
# 가상 예측 결과 생성
y_pred = np.random.randint(2, size=len(y_test))

# 4-1. wandb.Table로 예측 결과 상세 로깅
validation_table = wandb.Table(columns=["ID", "Prediction", "Ground Truth"])
for i in range(20): # 20개 샘플만 기록
    validation_table.add_data(i, y_pred[i], y_test[i])
wandb.log({"validation_results": validation_table})

# 4-2. matplotlib 그래프(Confusion Matrix) 로깅
cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm)
fig, ax = plt.subplots(figsize=(6, 6))
disp.plot(ax=ax)
plt.title("Confusion Matrix")
wandb.log({"confusion_matrix": fig})

# --- 5. 재현성을 위한 Artifacts 저장 ---
print("Saving artifacts...")

# 5-1. 모델 파일 저장 (가상)
model_filename = "dummy_model.pt"
with open(model_filename, "w") as f:
    f.write(f"Model trained with lr={config.learning_rate}")

model_artifact = wandb.Artifact(
    name=f"{run.id}-model",
    type="model",
    description="A dummy model trained for practice.",
    metadata={"epoch_trained": config.epochs, "lr": config.learning_rate}
)
model_artifact.add_file(model_filename)
run.log_artifact(model_artifact)

# 5-2. 소스 코드 저장
code_artifact = wandb.Artifact(
    name=f"{run.id}-code",
    type="code",
    description="The training script for this run."
)
# __file__은 현재 실행 중인 스크립트 파일의 경로입니다.
code_artifact.add_file(__file__, name="training_script.py")
run.log_artifact(code_artifact)

# --- 6. 실험 종료 ---
run.finish()
print("Run finished and synced to WandB.")
```
