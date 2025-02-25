# NVLink 상태 확인 스크립트

이 프로젝트는 Linux 환경에서 **NVIDIA NVLink** 연결 상태를 확인하는 스크립트입니다.  
GPU 간의 NVLink 연결을 탐색하고, 메모리 사용량 및 대역폭 정보를 출력합니다.

## 📌 기능

- **GPU 정보 출력**: GPU 개수, 이름, 메모리 사용량 등을 표시합니다.
- **NVLink 연결 확인**: GPU 간의 NVLink 연결 상태를 행렬로 출력합니다.
- **연결된 GPU 쌍 출력**: NVLink로 연결된 GPU와 대역폭을 표시합니다.
- **연결된 GPU 그룹 탐색**: NVLink로 연결된 GPU 그룹을 찾고, 그룹 내 총 VRAM을 출력합니다.
- **P2P 접근 여부 확인 (간소화된 방법)**: 오류 발생 시 대체 방법으로 P2P 접근 여부를 확인합니다.

## 🛠️ 설치 방법

### 1️⃣ 필수 패키지 설치

이 프로젝트를 실행하려면 `numpy`와 `pynvml` 패키지가 필요합니다.  
아래의 `requirements.txt`를 사용하여 패키지를 설치하세요:

```bash
pip install -r requirements.txt
```

또는 Conda 환경에서 실행하는 경우:

```bash
conda install numpy
pip install pynvml
```

⚠️ `pynvml` 패키지는 Conda 패키지로 제공되지 않으므로 `pip`로 설치해야 합니다.

### 2️⃣ NVIDIA NVML 라이브러리 설치

이 스크립트는 NVIDIA Management Library(NVML)를 사용하여 GPU 정보를 가져옵니다.  
**NVML은 NVIDIA 드라이버에 포함**되어 있으므로, **NVIDIA 드라이버가 설치되어 있어야 합니다**.

## 🚀 사용 방법

### 기본 실행

스크립트를 실행하려면 터미널에서 다음 명령을 입력하세요:

```bash
python nvlink_status.py
```

실행 결과로 다음과 같은 정보가 출력됩니다:

- **GPU 개수 및 정보**
- **각 GPU의 메모리 사용량**
- **NVLink 연결 상태 행렬**
- **NVLink로 연결된 GPU 쌍 및 대역폭 정보**
- **NVLink로 연결된 GPU 그룹 및 총 VRAM**

### 간소화된 NVLink 확인

만약 `check_nvlink_status()` 함수에서 오류가 발생하면,  
**간소화된 방법**(`check_nvlink_simplified()`)을 사용하여 NVLink 연결을 확인합니다.

## 📝 출력 예시

```
시스템에서 발견된 GPU 개수: 4
GPU 0: NVIDIA RTX 3090
  - VRAM: 총 24.00 GB, 사용 중 5.32 GB, 사용률: 22.2%
GPU 1: NVIDIA RTX 3090
  - VRAM: 총 24.00 GB, 사용 중 3.11 GB, 사용률: 12.9%
GPU 2: NVIDIA RTX 3090
  - VRAM: 총 24.00 GB, 사용 중 1.55 GB, 사용률: 6.5%
GPU 3: NVIDIA RTX 3090
  - VRAM: 총 24.00 GB, 사용 중 2.88 GB, 사용률: 11.9%

NVLink 연결 확인 중...
GPU 0의 NVLink 수: 2
  - NVLink 0는 GPU 0과 GPU 1 사이에 활성화됨 (버전: 3)
  - NVLink 1는 GPU 0과 GPU 2 사이에 활성화됨 (버전: 3)
...

NVLink 연결 행렬:
[[0 1 1 0]
 [1 0 0 1]
 [1 0 0 1]
 [0 1 1 0]]

NVLink로 연결된 GPU 쌍:
GPU 0 <-> GPU 1 (대역폭: 50 GB/s, 총 VRAM: 48.00 GB)
GPU 0 <-> GPU 2 (대역폭: 50 GB/s, 총 VRAM: 48.00 GB)
GPU 1 <-> GPU 3 (대역폭: 50 GB/s, 총 VRAM: 48.00 GB)
GPU 2 <-> GPU 3 (대역폭: 50 GB/s, 총 VRAM: 48.00 GB)

NVLink로 연결된 GPU 그룹:
그룹 1: GPU 0, GPU 1, GPU 2, GPU 3 (총 VRAM: 96.00 GB)
```

## 📌 파일 설명

| 파일명               | 설명 |
|----------------------|--------------------------------------------------|
| `nvlink_status.py`  | NVLink 연결 상태를 확인하는 메인 스크립트 |
| `requirements.txt`  | 필요한 패키지를 명시한 파일 (`numpy`, `pynvml`) |

## 📄 라이선스

이 프로젝트는 **MIT 라이선스** 하에 배포됩니다.
