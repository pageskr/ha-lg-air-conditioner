# LG Air Conditioner Integration for Home Assistant

LG 에어컨을 Home Assistant에서 제어할 수 있는 통합 구성요소입니다.

## 주요 기능

- **연결 방식**: Socket (직접 연결) 및 MQTT 지원
- **제어 기능**: 
  - 전원 on/off
  - 운전 모드 (냉방/난방/제습/송풍/자동)
  - 온도 설정 (18°C ~ 30°C)
  - 팬 속도 (저속/중속/고속/자동/정음/파워)
  - 스윙 모드 (고정/자동)
  - 잠금 기능
- **모니터링**:
  - 현재 온도
  - 설정 온도
  - 배관 온도 (1, 2)
  - 실외기 온도
  - 실외기 작동 상태
- **HACS 지원**: 손쉬운 설치 및 업데이트

## 지원 엔티티

### Climate (에어컨 제어)
- 전원, 모드, 온도, 팬속도, 스윙 통합 제어

### Binary Sensors (이진 센서)
- 전원 상태
- 잠금 상태
- 실외기 작동 상태

### Sensors (센서)
- 현재 온도
- 설정 온도
- 배관1 온도
- 배관2 온도
- 실외 온도
- 운전 모드
- 팬 속도
- 스윙 모드
- 원시 상태 데이터

### Switches (스위치)
- 전원 스위치
- 잠금 스위치

## 설치 방법

### HACS를 통한 설치 (권장)

1. HACS에서 "Integrations" 탭을 클릭합니다
2. 우측 상단의 메뉴(⋮)에서 "Custom repositories"를 선택합니다
3. 저장소 URL 추가:
   - Repository: `https://github.com/yourusername/ha-lg-air-conditioner`
   - Category: `Integration` 선택
4. "LG Air Conditioner"를 검색하여 설치합니다
5. Home Assistant를 재시작합니다

### 수동 설치

1. 이 저장소를 다운로드합니다
2. `custom_components/lg_air_conditioner` 폴더를 Home Assistant의 `custom_components` 디렉토리에 복사합니다
3. Home Assistant를 재시작합니다

## 설정 방법

### 통합 구성요소 추가

1. Home Assistant 설정 → 통합 구성요소 → 통합 구성요소 추가
2. "LG Air Conditioner" 검색
3. 연결 방식 선택:
   - **Socket**: 직접 IP 연결 (기본 포트: 8899)
   - **MQTT**: MQTT 브로커를 통한 연결

### Socket 모드 설정

- **호스트**: LG 에어컨 컨트롤러의 IP 주소
- **포트**: 통신 포트 (기본값: 8899)

### MQTT 모드 설정

- **브로커**: MQTT 브로커 주소
- **포트**: MQTT 포트 (기본값: 1883)
- **사용자명/비밀번호**: MQTT 인증 정보 (선택사항)
- **토픽**: 
  - 상태 수신: `ew11b/recv`
  - 명령 전송: `ew11b/send`

## 사용 방법

### Lovelace 카드 예시

```yaml
type: thermostat
entity: climate.lgac_01_cm
name: 거실 에어컨
```

### 자동화 예시

```yaml
automation:
  - alias: "에어컨 자동 제어"
    trigger:
      - platform: numeric_state
        entity_id: sensor.room_temperature
        above: 28
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.lgac_01_cm
        data:
          temperature: 24
          hvac_mode: cool
```

## 문제 해결

### 연결이 안 될 때

1. IP 주소와 포트가 올바른지 확인
2. 방화벽 설정 확인
3. MQTT의 경우 브로커 연결 상태 확인

### 상태가 업데이트되지 않을 때

1. 로그에서 오류 메시지 확인
2. 패킷 형식이 올바른지 확인
3. 체크섬 오류가 있는지 확인

## 기술 정보

### 통신 프로토콜

- 상태 요청: `8000A3{device}00{temp}{mode}{checksum}`
- 상태 응답: `1002A3{device}00{status}{mode}{temps...}{checksum}`
- 제어 명령: `8000A3{device}{status}{temp}{mode}{checksum}`

### 패킷 구조

- 상태 바이트: 2=off, 3=on, 6=off+lock, 7=on+lock
- 모드 바이트: HVAC(0-4) + 팬(0x10-0x60) + 스윙(0x08)
- 온도 인코딩: 설정온도 = 패킷값 + 15

## 기여하기

버그 리포트, 기능 요청, 풀 리퀘스트를 환영합니다!

## 라이선스

MIT License

## 제작자

Pages in Korea (pages.kr)

## 감사의 말

이 프로젝트는 LG 에어컨 사용자들의 편의를 위해 제작되었습니다.
