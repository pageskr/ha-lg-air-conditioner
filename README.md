# LG Air Conditioner for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

LG 에어컨을 Home Assistant에서 제어하기 위한 통합입니다.

## 기능

- Socket 및 MQTT 연결 방식 지원
- 최대 4대의 에어컨 제어
- 온도, 모드, 팬 속도 제어
- 상태 모니터링 (전원, 현재 온도, 설정 온도, 에러 코드, 필터 알람)
- HACS를 통한 쉬운 설치

## 설치

### HACS를 통한 설치 (권장)

1. HACS에서 "통합" 탭으로 이동
2. 우측 상단의 메뉴 버튼 (⋮) 클릭
3. "사용자 정의 저장소" 선택
4. 저장소 URL에 `https://github.com/pagesinkorea/ha-lg-air-conditioner` 입력
5. 카테고리는 "통합" 선택
6. "추가" 버튼 클릭
7. HACS 통합 탭에서 "LG Air Conditioner" 검색
8. "설치" 버튼 클릭
9. Home Assistant 재시작

### 수동 설치

1. `custom_components/lg_air_conditioner` 폴더를 Home Assistant의 `custom_components` 디렉토리에 복사
2. Home Assistant 재시작

## 구성

1. Home Assistant 설정 → 통합 → 통합 추가 → LG Air Conditioner 검색
2. 연결 방식 선택:
   - **Socket**: EW11 장치를 통한 직접 연결
   - **MQTT**: MQTT 브로커를 통한 연결
3. 선택한 방식에 따라 필요한 정보 입력

### Socket 설정
- 호스트 IP: EW11 장치의 IP 주소
- 포트: 8899 (기본값)
- 스캔 간격: 30초 (기본값)

### MQTT 설정
- MQTT 브로커 주소
- MQTT 포트: 1883 (기본값)
- 사용자명/비밀번호 (선택사항)
- 토픽 설정 (기본값 사용 권장)
- 스캔 간격: 30초 (기본값)

## 지원되는 기능

### Climate 엔티티
- 전원 켜기/끄기
- 모드 변경 (자동, 냉방, 난방, 제습, 송풍)
- 온도 설정 (18-30°C)
- 팬 속도 조절 (낮음, 중간, 높음, 자동, 파워, 자연풍)

### 센서
- 현재 온도
- 설정 온도
- 에러 코드

### 이진 센서
- 전원 상태
- 필터 알람

### 스위치
- 전원 켜기/끄기

## 프로토콜 정보

### 상태 요청 패킷
- 형식: `8000A3{device_num}`
- 예시: `8000A301` (1번 기기 상태 요청)

### 제어 패킷
- 형식: `8100C6{device_num}{power}{mode}{temp}{fan}0000000000000000000000`
- power: 00(끄기), 01(켜기)
- mode: 00(끄기), 01(난방), 02(냉방), 03(제습), 04(송풍), 05(자동)
- temp: 온도값 (16진수)
- fan: 00(낮음), 01(중간), 02(높음), 03(자동), 04(파워), 05(자연풍)

## 문제 해결

### Socket 연결 실패
- EW11 장치의 IP 주소가 올바른지 확인
- 포트 8899가 열려있는지 확인
- 방화벽 설정 확인

### MQTT 연결 실패
- MQTT 브로커가 실행 중인지 확인
- 사용자명/비밀번호가 올바른지 확인
- 토픽 권한 설정 확인

## 라이센스

MIT License

## 제작자

Pages in Korea (pages.kr)

## 기여

이슈 및 PR은 언제나 환영합니다!
