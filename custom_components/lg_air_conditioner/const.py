"""Constants for the LG Air Conditioner integration."""

DOMAIN = "lg_air_conditioner"

# Configuration constants
CONF_CONNECTION_TYPE = "connection_type"
CONF_SOCKET_HOST = "socket_host"
CONF_SOCKET_PORT = "socket_port"
CONF_MQTT_BROKER = "mqtt_broker"
CONF_MQTT_PORT = "mqtt_port"
CONF_MQTT_USERNAME = "mqtt_username"
CONF_MQTT_PASSWORD = "mqtt_password"
CONF_MQTT_TOPIC_STATE = "mqtt_topic_state"
CONF_MQTT_TOPIC_SEND = "mqtt_topic_send"
CONF_MQTT_TOPIC_RECV = "mqtt_topic_recv"
CONF_SCAN_INTERVAL = "scan_interval"

# Connection types
CONNECTION_TYPE_SOCKET = "socket"
CONNECTION_TYPE_MQTT = "mqtt"

# Default values
DEFAULT_SOCKET_PORT = 8899
DEFAULT_MQTT_PORT = 1883
DEFAULT_MQTT_TOPIC_STATE = "lgac/state/{device_num}"
DEFAULT_MQTT_TOPIC_SEND = "lgac/scan"
DEFAULT_MQTT_TOPIC_RECV = "ew11b/recv"
DEFAULT_SCAN_INTERVAL = 30

# Device constants
DEVICE_COUNT = 4
DEVICE_MANUFACTURER = "LG Electronics"
DEVICE_MODEL = "Air Conditioner"
DEVICE_NAME = "LG Air Conditioner"
DEVICE_INFO_NAME = "Pages in Korea (pages.kr)"

# Climate constants
SUPPORT_TARGET_TEMPERATURE = 1
SUPPORT_FAN_MODE = 8
SUPPORT_SWING_MODE = 16

# HVAC modes mapping
HVAC_MODE_MAP = {
    "00": "off",
    "01": "heat",
    "02": "cool",
    "03": "dry",
    "04": "fan_only",
    "05": "auto",
}

REVERSE_HVAC_MODE_MAP = {v: k for k, v in HVAC_MODE_MAP.items()}

# Fan modes mapping
FAN_MODE_MAP = {
    "00": "low",
    "01": "medium",
    "02": "high",
    "03": "auto",
    "04": "power",
    "05": "nature",
}

REVERSE_FAN_MODE_MAP = {v: k for k, v in FAN_MODE_MAP.items()}

# Packet constants
PACKET_PREFIX = "8000A3"
STATE_REQUEST_PACKET_FORMAT = "8000A3{device_num}"
CONTROL_PACKET_FORMAT = "8100C6{device_num}{power}{mode}{temp}{fan}0000000000000000000000"

# Power state
POWER_ON = "01"
POWER_OFF = "00"
