import network
import time
from umqtt.simple import MQTTClient

# WiFi Credentials (replace with your own)
SSID = "Two Girls One Router"
PASSWORD = "Pommesgesichter"

# MQTT Broker details (use your broker's IP address without any subnet mask)
MQTT_BROKER = "192.168.178.113"  # Replace with your Home Assistant IP
CLIENT_ID = "esp32-test"
TOPIC_ADC   = b"home/esp32/adc"
TOPIC_TEMP  = b"home/esp32/temp"
TOPIC_HUM   = b"home/esp32/hum"
TOPIC_STATUS = b"home/esp32/status"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.5)
    print("WiFi connected. IP:", wlan.ifconfig()[0])
    return wlan

def mqtt_connect(client):
    try:
        client.connect()
        print("Connected to MQTT broker")
        # Publish an initial status message
        client.publish(TOPIC_STATUS, b"ESP32 Test Online")
    except Exception as e:
        print("MQTT connection failed:", e)

# Connect to WiFi
connect_wifi()

# Setup MQTT client (no username/password required for anonymous connections)
mqtt_client = MQTTClient(CLIENT_ID, MQTT_BROKER, port=1883, user="SmartCarpet", password="smartcarpet")
mqtt_connect(mqtt_client)

while True:
    # Dummy test values
    dummy_adc = 123         # Example ADC reading
    dummy_temp = 30       # Example temperature in Celsius
    dummy_hum = 65.0        # Example humidity percentage

    # Publish dummy values to MQTT topics (encoded as strings)
    mqtt_client.publish(TOPIC_ADC, str(dummy_adc).encode())
    mqtt_client.publish(TOPIC_TEMP, str(dummy_temp).encode())
    mqtt_client.publish(TOPIC_HUM, str(dummy_hum).encode())

    print("Published dummy values: ADC={}, Temp={}, Hum={}".format(dummy_adc, dummy_temp, dummy_hum))
    time.sleep(5)