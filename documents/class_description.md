# 파이썬 클래스(Class)

안녕하세요! 오늘은 파이썬의 가장 중요한 개념 중 하나인 '클래스(Class)'에 대해 깊이 있게 알아보겠습니다. 많은 분들이 함수까지는 익숙하지만 클래스는 어렵게 느끼곤 합니다. 하지만 딥러닝, 특히 PyTorch로 모델을 만들려면 클래스는 선택이 아닌 필수입니다. 오늘 수업을 통해 클래스가 왜 필요하고, 어떻게 사용하며, 딥러닝 모델링에 어떻게 적용되는지 확실히 이해하게 될 거예요!

---

## 1. 클래스가 뭔가요? - 붕어빵 틀과 붕어빵

가장 먼저, 간단한 질문으로 시작해 볼게요.

> **"여러분, 붕어빵은 어떻게 만들어지나요?"**

네, 맞아요. **붕어빵 '틀'**이 있어야 하죠. 밀가루 반죽과 팥을 넣고 찍어내면 맛있는 붕어빵이 완성됩니다.

여기서 **클래스 (Class)**는 바로 **붕어빵 틀**과 같습니다.
그리고 그 틀로 만들어낸 각각의 **붕어빵**이 바로 **객체 (Object) 또는 인스턴스 (Instance)**입니다.

-   **클래스 (Class)**: 객체를 만들기 위한 **설계도** 또는 **틀**. 어떤 속성(데이터)과 행동(기능)을 가질지 정의합니다.
-   **객체 (Object/Instance)**: 클래스라는 설계도를 바탕으로 메모리에 **실체화된 것**. 실제로 데이터를 담고, 기능을 수행하는 실체입니다.

하나의 '붕어빵 틀(클래스)'이 있으면, 속을 다르게(팥, 슈크림, 피자...) 해서 수많은 '붕어빵(객체)'을 만들 수 있겠죠? 이게 바로 클래스의 핵심 아이디어입니다.

```python
# '붕어빵 틀'을 만들어 봅시다!
class Bungeoppang:
    # 붕어빵이 만들어질 때(객체가 생성될 때) 실행되는 부분
    def __init__(self, taste):
        self.taste = taste  # 이 붕어빵의 '맛'이라는 속성(데이터)
        print(f"{self.taste} 맛 붕어빵이 만들어졌어요!")

    # 붕어빵의 행동(기능)
    def eat(self):
        print(f"{self.taste} 맛 붕어빵을 맛있게 먹습니다. 냠냠!")

# '붕어빵 틀'로 실제 '붕어빵'을 만들어 볼까요?
red_bean_bb = Bungeoppang("팥")      # '팥' 맛 붕어빵 객체 생성
cream_bb = Bungeoppang("슈크림")  # '슈크림' 맛 붕어빵 객체 생성

# 각 붕어빵은 고유의 맛(상태)을 가집니다.
print(f"첫 번째 붕어빵의 맛: {red_bean_bb.taste}")

# 각 붕어빵은 '먹기'라는 행동을 할 수 있습니다.
red_bean_bb.eat()
cream_bb.eat()
```

## 2. 왜 클래스를 써야 할까요? (함수 vs 클래스)

"그냥 함수 여러 개 만들어서 쓰면 안 되나요?" 좋은 질문입니다. 간단한 작업은 함수만으로 충분하지만, 프로그램이 복잡해지면 한계에 부딪힙니다.

**상황**: 게임 캐릭터의 정보(체력, 마나)와 행동(공격)을 관리해야 한다고 상상해 봅시다.

#### 함수만 사용할 경우

```python
# 캐릭터 1의 데이터
character1_hp = 100
character1_power = 10

# 캐릭터 2의 데이터
character2_hp = 120
character2_power = 8

# 캐릭터의 행동을 정의하는 함수들
def attack(attacker_power, defender_hp):
    defender_hp -= attacker_power
    return defender_hp

# 게임 플레이
character2_hp = attack(character1_power, character2_hp)
print(f"캐릭터 2의 남은 체력: {character2_hp}")
```

**문제점:**
1.  **데이터와 기능이 분리되어 있습니다.** 캐릭터의 체력(`hp`)과 공격력(`power`) 데이터가 `attack`이라는 기능과 따로 놀고 있죠.
2.  캐릭터가 100명이라면? `character100_hp`, `character100_power`... 변수가 수백 개가 되어 관리가 불가능해집니다.
3.  코드가 직관적이지 않습니다. (`attack` 함수의 주체와 대상이 명확하지 않음)

#### 클래스를 사용할 경우

```python
class GameCharacter:
    # 캐릭터의 설계도
    def __init__(self, name, hp, power):
        self.name = name    # 속성 1: 이름
        self.hp = hp        # 속성 2: 체력
        self.power = power  # 속성 3: 공격력
        print(f"{self.name} 캐릭터 생성!")

    # 캐릭터의 행동(메서드)
    def attack(self, target):
        print(f"{self.name}이(가) {target.name}을(를) 공격!")
        target.hp -= self.power

    def show_status(self):
        print(f"{self.name}의 현재 체력: {self.hp}")

# 설계도로 실제 캐릭터(객체)를 만듭니다.
char1 = GameCharacter("전사", 100, 10)
char2 = GameCharacter("마법사", 80, 15)

# 게임 플레이
char1.attack(char2) # char1이 char2를 공격 (코드가 훨씬 직관적!)
char2.show_status()
```

**클래스의 장점:**
1.  **데이터와 기능을 하나로 묶어줍니다 (캡슐화).** `GameCharacter` 클래스 안에 캐릭터의 정보(`hp`, `power`)와 행동(`attack`)이 함께 들어있어 관리가 편합니다.
2.  **재사용성이 극대화됩니다.** 새로운 캐릭터가 필요하면 `GameCharacter(...)` 한 줄로 쉽게 찍어낼 수 있습니다.
3.  코드가 직관적이고 명확해집니다. `char1.attack(char2)`는 'char1'이 'attack'이라는 행동을 'char2'에게 한다는 의미가 명확하게 전달됩니다.
   
결론적으로, 클래스는 **관련 있는 데이터(상태)와 행동(기능)을 하나의 덩어리로 묶어 관리**하기 위해 사용합니다.


---

## 3. 딥러닝에서의 클래스 (feat. PyTorch)

이제 진짜 중요한 질문입니다. "왜 PyTorch로 모델을 만들 때 항상 `class MyModel(nn.Module):` 형태로 만들까요?"

정답은 **'딥러닝 모델'이야말로 클래스로 표현하기 가장 완벽한 대상**이기 때문입니다. 딥러닝 모델은 단순한 함수가 아니라, 내부에 **상태**를 가지는 복잡한 객체입니다.

#### 이유 1: 학습 가능한 파라미터(가중치)라는 '상태'를 가져야 한다!

-   신경망의 레이어(e.g., `nn.Linear`)는 입력이 들어왔을 때 단순히 계산만 하고 끝나는 함수가 아닙니다. 내부에 **가중치(weights)**와 **편향(bias)**이라는 **상태**를 가지고 있어야 합니다.
-   이 **상태**는 학습 과정에서 계속 업데이트되어야 합니다.
-   클래스는 `self.weight`와 같이 객체의 속성으로 이 **상태**를 저장하고 관리하기에 완벽한 구조입니다. 함수는 이런 **상태**를 기억할 수 없습니다.

#### 이유 2: 복잡한 구조를 '부품'처럼 조립할 수 있다!

-   현대 딥러닝 모델은 수많은 레이어를 조합하여 만듭니다. ResNet의 `Bottleneck` 블록처럼, 특정 구조가 반복적으로 사용되기도 합니다.
-   클래스를 사용하면 이런 작은 블록(레이어)들을 하나의 부품처럼 미리 정의해두고, `__init__` (생성자)에서 이 부품들을 조립하여 더 큰 모델을 쉽게 만들 수 있습니다.

#### 이유 3: 상속을 통해 강력한 기능을 물려받는다!

-   우리가 `class MyModel(nn.Module):` 이라고 쓰는 것은, PyTorch가 미리 만들어 놓은 강력한 `nn.Module` 클래스의 모든 기능을 **상속**받겠다는 의미입니다.
-   상속 덕분에 우리는 복잡한 내부 동작을 몰라도 `.to(device)`, `.parameters()`(모든 학습 파라미터를 반환), `.train()`(학습 모드로 전환), `.eval()`(평가 모드로 전환) 같은 수많은 편의 기능을 그냥 가져다 쓸 수 있습니다.

```python
import torch
import torch.nn as nn

# nn.Module이라는 설계도를 상속받아 우리만의 모델 설계도를 만듭니다.
class SimpleModel(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super().__init__() # 주의: 부모 클래스(nn.Module)의 생성자를 반드시 호출!

        # 1. 모델의 '상태'가 될 부품(레이어)들을 정의합니다.
        #    이 레이어들은 내부에 학습 가능한 파라미터(가중치)를 가집니다.
        self.layer1 = nn.Linear(input_size, hidden_size)
        self.activation = nn.ReLU()
        self.layer2 = nn.Linear(hidden_size, output_size)

    # 2. 데이터가 들어왔을 때의 계산 흐름(순전파)을 정의합니다.
    def forward(self, x):
        x = self.layer1(x)
        x = self.activation(x)
        x = self.layer2(x)
        return x

# 모델(객체) 생성
model = SimpleModel(input_size=784, hidden_size=256, output_size=10)
print(model)
```

---

## 4. 딥러닝 모듈 제작 가이드

이제 여러분이 직접 커스텀 레이어나 모델을 만들 차례입니다. 단순히 동작하는 코드를 넘어, 효율적이고 견고한 모듈을 만들기 위해 반드시 알아야 할 핵심 원칙과 실무 Best Practice를 알아보겠습니다.

### **Part 1: 반드시 지켜야 할 핵심 원칙**

이 원칙들은 모델이 올바르게 동작하기 위한 최소한의 필수 요건입니다.

#### **원칙 1: `__init__`은 설계실, `forward`는 조립 라인**

모델 클래스의 두 핵심 메서드는 역할이 명확하게 분리되어야 합니다.

-   **`__init__` (설계실)**: 모델에 필요한 부품들(`nn.Linear`, `nn.Conv2d` 등)을 **정의하고 초기화**하는 공간입니다. 모델 객체가 생성될 때 **단 한 번** 실행됩니다.
-   **`forward` (조립 라인)**: 실제 데이터가 입력으로 들어왔을 때, `__init__`에서 준비한 부품들을 **어떤 순서로 거치게 할지 계산 흐름을 정의**하는 공간입니다. 데이터가 모델을 통과할 때마다 호출됩니다.
-   ⚠️ **매우 중요**: `forward` 메서드 안에서 레이어를 정의하면(`self.layer = nn.Linear(...)`) 안 됩니다. 매 순전파마다 새로운 파라미터가 생성되어 학습이 전혀 이루어지지 않고, 엄청난 성능 저하를 유발합니다.

---

#### **원칙 2: `super().__init__()` - 부모 클래스와의 필수 연결고리**

`__init__` 메서드의 첫 줄에 `super().__init__()`를 쓰는 것은 단순한 관례가 아닌, **상속의 핵심 원리**입니다.



'기본 붕어빵 틀(`nn.Module`)'을 상속받아 '피자 붕어빵 틀(`MyModel`)'을 만든다고 상상해 보세요. `super().__init__()`는 **"일단 기본 붕어빵 틀의 기능(열선, 손잡이 등)부터 먼저 준비해 줘!"**라고 요청하는 것과 같습니다. 이 과정이 없으면, PyTorch는 우리가 만든 클래스를 신경망 모듈로 인식조차 못 합니다.

`nn.Module`의 `__init__`은 내부적으로 다음과 같은 **핵심 준비 작업**을 수행합니다.
-   **파라미터 저장소 준비**: 모델의 모든 학습 가능한 파라미터(`weight`, `bias`)를 추적할 수 있는 공간(`_parameters`, `_modules`)을 초기화합니다.
-   **다양한 헬퍼 기능 활성화**: `.to(device)`, `.parameters()` 등 우리가 편리하게 사용하는 기능들을 활성화합니다.

만약 `super().__init__()`를 호출하지 않으면 이 모든 준비 작업이 생략되어, 모델의 파라미터가 등록되지 않고 결국 모델은 전혀 학습되지 않습니다.

```python
import torch.nn as nn

class BadModel(nn.Module):
    def __init__(self):
        # super().__init__() 호출을 깜빡했다!
        self.layer = nn.Linear(10, 5)

class GoodModel(nn.Module):
    def __init__(self):
        super().__init__() # 정상적으로 부모 클래스의 기능을 물려받음
        self.layer = nn.Linear(10, 5)

# 나쁜 예: 파라미터가 비어있음
bad_model = BadModel()
print(f"Bad Model Parameters: {list(bad_model.parameters())}")
# 출력: Bad Model Parameters: []

# 좋은 예: 파라미터가 정상적으로 등록됨
good_model = GoodModel()
print(f"Good Model Parameters: {len(list(good_model.parameters())) > 0}")
# 출력: Good Model Parameters: True
```

물론입니다. 요청하신 대로 이모티콘을 최소화하고, 전체 내용을 하나의 Markdown 코드 블록으로 다시 작성해 드리겠습니다.

아래 상자 안의 모든 텍스트를 복사하여 .md 파일에 붙여넣으시면 됩니다.

Markdown

## 4. 실전! 나만의 딥러닝 모듈 제작 가이드

이제 여러분이 직접 커스텀 레이어나 모델을 만들 차례입니다. 단순히 동작하는 코드를 넘어, 효율적이고 견고한 모듈을 만들기 위해 반드시 알아야 할 핵심 원칙과 실무 Best Practice를 알아보겠습니다.

### **Part 1: 반드시 지켜야 할 핵심 원칙**

이 원칙들은 모델이 올바르게 동작하기 위한 최소한의 필수 요건입니다.

#### **원칙 1: `__init__`은 설계실, `forward`는 조립 라인**

모델 클래스의 두 핵심 메서드는 역할이 명확하게 분리되어야 합니다.

-   **`__init__` (설계실)**: 모델에 필요한 부품들(`nn.Linear`, `nn.Conv2d` 등)을 **정의하고 초기화**하는 공간입니다. 모델 객체가 생성될 때 **단 한 번** 실행됩니다.
-   **`forward` (조립 라인)**: 실제 데이터가 입력으로 들어왔을 때, `__init__`에서 준비한 부품들을 **어떤 순서로 거치게 할지 계산 흐름을 정의**하는 공간입니다. 데이터가 모델을 통과할 때마다 호출됩니다.
-   ⚠️ **매우 중요**: `forward` 메서드 안에서 레이어를 정의하면(`self.layer = nn.Linear(...)`) 안 됩니다. 매 순전파마다 새로운 파라미터가 생성되어 학습이 전혀 이루어지지 않고, 엄청난 성능 저하를 유발합니다.

---

#### **원칙 2: `super().__init__()` - 부모 클래스와의 필수 연결고리**

`__init__` 메서드의 첫 줄에 `super().__init__()`를 쓰는 것은 단순한 관례가 아닌, **상속의 핵심 원리**입니다.



'기본 붕어빵 틀(`nn.Module`)'을 상속받아 '피자 붕어빵 틀(`MyModel`)'을 만든다고 상상해 보세요. `super().__init__()`는 **"일단 기본 붕어빵 틀의 기능(열선, 손잡이 등)부터 먼저 준비해 줘!"**라고 요청하는 것과 같습니다. 이 과정이 없으면, PyTorch는 우리가 만든 클래스를 신경망 모듈로 인식조차 못 합니다.

`nn.Module`의 `__init__`은 내부적으로 다음과 같은 **핵심 준비 작업**을 수행합니다.
-   **파라미터 저장소 준비**: 모델의 모든 학습 가능한 파라미터(`weight`, `bias`)를 추적할 수 있는 공간(`_parameters`, `_modules`)을 초기화합니다.
-   **다양한 헬퍼 기능 활성화**: `.to(device)`, `.parameters()` 등 우리가 편리하게 사용하는 기능들을 활성화합니다.

만약 `super().__init__()`를 호출하지 않으면 이 모든 준비 작업이 생략되어, 모델의 파라미터가 등록되지 않고 결국 모델은 전혀 학습되지 않습니다.

```python
import torch.nn as nn

class BadModel(nn.Module):
    def __init__(self):
        # super().__init__() 호출을 깜빡했다!
        self.layer = nn.Linear(10, 5)

class GoodModel(nn.Module):
    def __init__(self):
        super().__init__() # 정상적으로 부모 클래스의 기능을 물려받음
        self.layer = nn.Linear(10, 5)

# 나쁜 예: 파라미터가 비어있음
bad_model = BadModel()
print(f"Bad Model Parameters: {list(bad_model.parameters())}")
# 출력: Bad Model Parameters: []

# 좋은 예: 파라미터가 정상적으로 등록됨
good_model = GoodModel()
print(f"Good Model Parameters: {len(list(good_model.parameters())) > 0}")
# 출력: Good Model Parameters: True
```

---

#### 원칙 3: 모든 것이 클래스일 필요는 없다! (함수 vs. 클래스)
클래스는 강력하지만, 모든 곳에 사용할 필요는 없습니다. 핵심적인 구분 기준은 '**상태(State)**'의 유무입니다.

- **클래스를 사용할 때**: 내부에 학습 가능한 파라미터와 같이 지속적으로 유지하고 업데이트해야 할 '상태'가 있을 때 사용합니다. (e.g., `nn.Linear`, `ResNet` 모델)

- **함수를 사용할 때**: 입력값을 받아 정해진 계산을 수행하고 결과를 반환하는, '상태'가 필요 없는 일회성 작업에 사용합니다. (e.g., `ReLU` 활성화 함수, `PICP` 같은 평가 지표)

```python
# GOOD: '상태'가 필요 없는 평가 지표는 간단한 함수로 구현하는 것이 가장 좋다.
def calculate_picp(true, pred):
    p10 = pred[:,:,0].unsqueeze(-1)
    p90 = pred[:,:,-1].unsqueeze(-1)
    mask_matrix = ((true >= p10) & (true <= p90)).float()
    picp = mask_matrix.mean()
    return picp.item()
```

---


### **Part 2: 실무자를 위한 코드 설계 Best Practice**
핵심 원칙을 익혔다면, 이제 더 나아가 협업과 유지보수에 용이한 '프로페셔널한' 코드를 작성하는 방법을 알아봅시다.

#### **유지보수와 가독성을 높이는 설계**
- **단일 책임 원칙**: 클래스는 하나의 명확한 목적만 가져야 합니다. Model 클래스는 모델 구조에만 집중하고, 데이터 로딩(Dataset)이나 학습 과정(Trainer)은 별도의 클래스로 분리하세요.

- **설정(Config) 분리**: hidden_size와 같은 하이퍼파라미터를 클래스 내부에 하드코딩하지 마세요. __init__의 인자로 받아 유연하고 재사용하기 쉽게 만들어야 합니다.

```python
# Good: 유연하고 재사용이 쉽다
class MyModel(nn.Module):
    def __init__(self, input_size: int, hidden_size: int, num_classes: int):
        super().__init__()
        self.layer1 = nn.Linear(input_size, hidden_size)
        self.layer2 = nn.Linear(hidden_size, num_classes)

# model = MyModel(input_size=784, hidden_size=512, num_classes=10) # 원하는 값으로 쉽게 생성
```

#### **견고함과 자동 검증**
- **타입 힌트 (Type Hinting) 적극 사용**: `input_size: int`처럼 변수의 타입을 명시하면 코드의 가독성이 높아지고, 실행 전부터 잠재적인 오류를 쉽게 찾을 수 있습니다.

- **Assertion으로 입력 검증**: `forward` 메서드 초입에서 `assert x.ndim == 2`와 같이 입력 데이터의 형태를 검증하는 습관은, 원인 모를 에러를 방지하고 디버깅 시간을 획기적으로 줄여줍니다.

```Python
import torch

def forward(self, x: torch.Tensor) -> torch.Tensor:
    # 입력 x가 2D 텐서(batch_size, features)인지 검증
    assert x.ndim == 2, f"Expected 2D tensor, but got {x.ndim}D tensor."
    # ... 이후 순전파 로직 ...
    return x
```