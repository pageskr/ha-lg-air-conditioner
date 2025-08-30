# LG Air Conditioner for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

LG 에어컨을 Home Assistant에서 제어하기 위한 통합입니다.

## 기능

- Socket 및 MQTT 연결 방식 지원
- 최대 4대의 에어컨 동시 제어
- 온도, 모드, 팬 속도, 스윙 모드 제어
- 실시간 상태 모니터링
- 잠금/해제 기능
- HACS를 통한 쉬운 설치

## 지원되는 엔티티

### Climate 엔티티
- 전원 켜기/끄기
- 운전 모드 변경 (자동, 냉방, 난방, 제습, 송풍)
- 온도 설정 (18-30°C)
- 팬 속도 조절 (낮음, 중간, 높음, 자동, 저소음, 파워)
- 스윙 모드 (고정, 자동)

### 센서
- 현재 온도
- 설정 온도
- 배관1 온도
- 배관2 온도
- 실외 온도
- 운전 모드
- 팬 속도
- 스윙 모드
- 에러 코드

### 이진 센서
- 전원 상태
- 필터 알람
- 잠금 상태

### 스위치
- 전원 켜기/끄기
- 잠금/해제

## 설치

### HACS를 통한 설치 (권장)

1. HACS에서 "통합" 탭으로 이동
2. 우측 상단의 메뉴 버튼 (⋮) 클릭
3. "사용자 정의 저장소" 선택
4. 저장소 URL에 `https://github.com/pageskr/ha-lg-air-conditioner` 입력
5. 카테고리는 "통합" 선택
6. "추가" 버튼 클릭
7. HACS 통합 탭에서 "LG Air Conditioner" 검색
8. "설치" 버튼 클릭
9. Home Assistant 재시작

### 수동 설치

1. 이 저장소의 `custom_components/lg_air_conditioner` 폴더를 Home Assistant의 `custom_components` 디렉토리에 복사
2. Home Assistant 재시작

## 구성

### 1단계: 통합 추가

1. Home Assistant 설정 → 통합 → 통합 추가
2. "LG Air Conditioner" 검색
3. 통합 추가 클릭

### 2단계: 연결 방식 선택

#### Socket 모드 (직접 연결)
- EW11 장치를 통한 직접 TCP/IP 연결
- 필요한 정보:
  - 호스트 IP: EW11 장치의 IP 주소
  - 포트: 8899 (기본값)
  - 스캔 간격: 30초 (기본값)

#### MQTT 모드 (브로커 경유)
- MQTT 브로커를 통한 연결
- 필요한 정보:
  - MQTT 브로커 주소
  - MQTT 포트: 1883 (기본값)
  - 사용자명/비밀번호 (선택사항)
  - 토픽 설정:
    - 상태 토픽: `lgac/state/{device_num}` (기본값)
    - 명령 전송 토픽: `lgac/scan` (기본값)
    - 데이터 수신 토픽: `ew11b/recv` (기본값)
  - 스캔 간격: 30초 (기본값)

### 3단계: 설정 변경

통합 추가 후 설정 버튼을 클릭하여 연결 정보를 변경할 수 있습니다.

## 프로토콜 정보

### 상태 요청 패킷
```
형식: 8000A3{device_num}
예시: 8000A301 (1번 기기 상태 요청)
```

### 상태 응답 패킷
```
형식: 10{source}A300{device_num}00{status}{opermode}{set_temp}{current_temp}{pipe1_temp}{pipe2_temp}{outdoor_temp}...{checksum}

위치별 데이터 (16진수 2자리씩):
- 00-01: 10 (헤더)
- 02-03: source (송신 기기 번호)
- 04-05: A3 (메시지 타입)
- 06-07: 00
- 08-09: device_num (대상 기기 번호: 01-04)
- 10-11: 00
- 12-13: status (전원/잠금 상태)
  - 02: 전원 OFF, 잠금 OFF
  - 03: 전원 OFF, 잠금 ON
  - 06: 전원 ON, 잠금 ON
  - 07: 전원 ON, 잠금 OFF
- 14-15: opermode (운전모드 복합값)
  - bit 0-2: HVAC 모드 (0=냉방, 1=제습, 2=송풍, 3=자동, 4=난방)
  - bit 3: 스윙 모드 (0=고정, 1=자동)
  - bit 4-6: 팬 모드 (1=낮음, 2=중간, 3=높음, 4=자동, 5=저소음, 6=파워)
- 16-17: set_temp (설정 온도 - 15)
- 18-19: current_temp (현재 온도 raw 값)
- 20-21: pipe1_temp (배관1 온도 raw 값)
- 22-23: pipe2_temp (배관2 온도 raw 값)
- 24-25: outdoor_temp (실외 온도 raw 값)
- 30-31: checksum

온도 계산식: 실제온도 = 64 - (raw값 / 3)
체크섬 계산: 
  - sum = 모든 바이트 합계 (체크섬 제외)
  - checksum = (sum & 0xAA) + (85 - (sum & 0x55))
```

### 제어 패킷
```
형식: 8000A3{device_num}{status}{opermode}{temperature}{checksum}

예시: 8000A301070A0DC5
- device_num: 01 (1번 기기)
- status: 07 (전원 ON, 잠금 OFF)
- opermode: 0A (냉방 + 팬 자동 + 스윙 고정)
- temperature: 0D (설정온도 28°C = 28-15 = 13 = 0x0D)
- checksum: C5
```

## 문제 해결

### Socket 연결 실패
- EW11 장치의 IP 주소가 올바른지 확인
- 포트 8899가 열려있는지 확인
- 방화벽 설정 확인
- EW11 장치와 Home Assistant가 같은 네트워크에 있는지 확인

### MQTT 연결 실패
- MQTT 브로커가 실행 중인지 확인
- 사용자명/비밀번호가 올바른지 확인
- 토픽 권한 설정 확인
- MQTT 브로커 로그 확인

### 상태가 업데이트되지 않음
- 로그에서 "hex parsing state" 메시지 확인
- 수신되는 패킷이 "10XXA3"으로 시작하는지 확인
- lgac_forward.py가 실행 중인지 확인 (MQTT 모드)
- 체크섬 검증 실패 시 패킷이 무시될 수 있음

## 로그 확인

디버그 로그를 활성화하려면 `configuration.yaml`에 다음 추가:

```yaml
logger:
  default: info
  logs:
    custom_components.lg_air_conditioner: debug
```

## 호환성

- Home Assistant 2023.0.0 이상
- Python 3.9 이상
- MQTT 모드 사용 시 MQTT 브로커 필요
- Socket 모드 사용 시 EW11 또는 호환 장치 필요

## 라이센스

MIT License

## 제작자

Pages in Korea (pages.kr)

## 기여

이슈 및 PR은 언제나 환영합니다!

### 기여 방법
1. 이 저장소를 Fork
2. 새로운 기능 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add some amazing feature'`)
4. 브랜치에 푸시 (`git push origin feature/amazing-feature`)
5. Pull Request 생성

## 변경 내역

### v1.0.1 (2025-08-30)
- 패킷 구조 분석 개선
- 스윙 모드 지원 추가
- 잠금/해제 기능 추가
- 배관 및 실외 온도 센서 추가
- 체크섬 검증 로직 구현
- 설정 변경 기능 추가

### v1.0.0 (2025-08-30)
- 최초 릴리스
- Socket 및 MQTT 연결 지원
- 4대 기기 동시 제어
- Climate, Sensor, Binary Sensor, Switch 엔티티 지원
- HACS 호환성 추가
