import paho.mqtt.client as mqtt
import binascii
import logging
import os
from logging.handlers import TimedRotatingFileHandler
import json

# 로깅 설정
logger = logging.getLogger('lgac_forward')
logger.setLevel(logging.DEBUG)

# 현재 파이썬 파일의 절대 경로를 기준으로 로그 파일 경로 설정
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
log_dir = os.path.join(current_dir, 'log')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'lgac_forward.log')

# 파일 핸들러와 포매터 설정
formatter = logging.Formatter(fmt="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
file_handler = TimedRotatingFileHandler(log_file, when="midnight", backupCount=7)
file_handler.setFormatter(formatter)
file_handler.suffix = "%Y%m%d"
logger.addHandler(file_handler)

# 콘솔 핸들러 설정 (필요할 경우)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# 최근 값을 저장할 딕셔너리
last_values = {
    "lgac/state/01": None,
    "lgac/state/02": None,
    "lgac/state/03": None,
    "lgac/state/04": None,
}

# 16진수 문자열을 바이너리 데이터로 변환하는 함수
def hex_to_binary(hex_str):
    try:
        return binascii.unhexlify(hex_str)
    except binascii.Error as e:
        logger.error(f"Error converting hex to binary: {e}")
        return None

# 바이너리 데이터를 16진수 문자열로 변환하는 함수
def binary_to_hex(packet):
    return binascii.hexlify(packet).decode('utf-8')

# MQTT 메시지를 수신할 때 호출되는 콜백 함수 (lgac/send)
def on_message_send(client, userdata, msg):
    logger.debug(f"Received message on topic: {msg.topic}")
    hex_data = msg.payload.decode('utf-8')
    logger.debug(f"Received hex data: {hex_data}")

    binary_data = hex_to_binary(hex_data)
    if binary_data is None:
        logger.error("Error: Failed to convert hex data to binary.")
        return

    logger.debug(f"Converted Binary data: {binary_data}")

    # 변환된 메시지를 다른 토픽으로 전송
    client.publish("ew11b/send", binary_data)
    logger.debug(f"Published message to topic: ew11b/send")

# MQTT 메시지를 수신할 때 호출되는 콜백 함수 (ew11b/recv)
def on_message_recv(client, userdata, msg):
    logger.debug(f"Received message on topic: {msg.topic}")
    logger.debug(f"Received raw binary data: {msg.payload}")
    hex_data = binary_to_hex(msg.payload)
    logger.debug(f"Converted hex data: {hex_data}")

    if len(hex_data) < 32:
        logger.error("Error: hex data is less than 32 characters.")
        return
    elif len(hex_data) > 32:
        hex_data = hex_data[:32]

    sequence_number = hex_data[8:10]
    state_topic = f"lgac/state/{sequence_number}"
    
    # 값이 변경된 경우
    if last_values.get(state_topic) != hex_data:
        last_values[state_topic] = hex_data

        # 변환된 메시지를 다른 토픽으로 전송
        client.publish(state_topic, hex_data)
        logger.debug(f"Published converted message to topic: {state_topic}")

# MQTT 클라이언트 초기화 함수
def init_connect():
    client = mqtt.Client()

    # 콜백 함수 설정
    client.message_callback_add("lgac/scan", on_message_send)
    client.message_callback_add("ew11b/recv", on_message_recv)

    # MQTT 브로커 설정
    client.connect("192.168.0.2")
    client.subscribe("lgac/scan")
    client.subscribe("ew11b/recv")

    return client

# Home Assistant에 MQTT Discovery 메시지 전송
def send_homeassistant_discovery(client):
    discovery_prefix = "homeassistant"
    device_name = "LG AC"
    sensors = [
        {"name": "01 Scan", "topic": "lgac/state/01", "sensor_id": "lgac_01_scan"},
        {"name": "02 Scan", "topic": "lgac/state/02", "sensor_id": "lgac_02_scan"},
        {"name": "03 Scan", "topic": "lgac/state/03", "sensor_id": "lgac_03_scan"},
        {"name": "04 Scan", "topic": "lgac/state/04", "sensor_id": "lgac_04_scan"},
    ]

    for sensor in sensors:
        config_topic = f"{discovery_prefix}/sensor/{sensor['sensor_id']}/config"
        config_payload = {
            "name": sensor['name'],
            "icon": "mdi:magnify-scan",
            "state_topic": sensor['topic'],
            "unique_id": sensor['sensor_id'],
            "device": {
                "identifiers": [device_name],
                "name": device_name,
                "model": "Air Conditioner",
                "manufacturer": "LG Electronics"
            }
        }
        client.publish(config_topic, json.dumps(config_payload), retain=True)
        logger.debug(f"Published Home Assistant discovery message for {sensor['sensor_id']}")

# 메인 함수
if __name__ == "__main__":
    client = init_connect()
    send_homeassistant_discovery(client)
    try:
        client.loop_forever()
    except Exception as e:
        logger.exception("Daemon finished!")
