# mqtt_connection.py
import network
import time
from umqtt.simple import MQTTClient

# WiFi Credentials
SSID = "Two Girls One Router"
PASSWORD = "Pommesgesichter"

# MQTT Broker details
MQTT_BROKER = "192.168.178.113"  # Replace with your Home Assistant IP
CLIENT_ID = "esp32-test"
MQTT_PORT = 1883
MQTT_USER = "SmartCarpet"      # If needed
MQTT_PASS = "smartcarpet"      # If needed






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

def mqtt_connect():
    """
    Creates and connects an MQTT client.
    Returns the connected client or None if connection fails.
    """
    client = MQTTClient(CLIENT_ID, MQTT_BROKER, port=MQTT_PORT, user=MQTT_USER, password=MQTT_PASS)
    try:
        client.connect()
        print("Connected to MQTT broker:", MQTT_BROKER)
    except Exception as e:
        print("MQTT connection failed:", e)
        client = None
    return client

def publish_data(client, topic, payload):
    """
    Publishes data to a given topic using the provided MQTT client.
    Topics and payloads are passed from the main file.
    """
    if client:
        try:
            client.publish(topic, payload)
            # Uncomment the following line for debugging if desired:
            # print("Published to topic:", topic, "Payload:", payload)
        except Exception as e:
            print("Failed to publish:", e)
    else:
        print("MQTT client is not connected. Data not published.")

# This part is for getting the Information back from SmartHome
received_temperature = None
received_transport_info = None


def mqtt_subscribe(client):
    """Subscribe to Home Assistant topics and handle received messages."""
    topics = [b"esp32c6/wetter", b"esp32c6/transport"]  # Added transport topic

    def message_callback(topic, msg):
        topic_str = topic.decode()
        msg_decoded = msg.decode()

        if topic_str == "esp32c6/wetter":
            process_temperature_message(msg_decoded)
        elif topic_str == "esp32c6/transport":
            process_transport_message(msg_decoded)

    client.set_callback(message_callback)

    for topic in topics:
        client.subscribe(topic)
        print("Subscribed to topic:", topic.decode())



def process_temperature_message(msg):
    """Process received MQTT messages and store the temperature."""
    global received_temperature  # Use the global variable
    try:
        received_temperature = float(msg)  # Convert message to float
        print("Received temperature:", received_temperature)
    except ValueError:
        print("Received non-numeric message, ignoring.")

def process_transport_message(msg):
    """Process received transport messages and store the time."""
    global received_transport_info
    try:
        received_transport_info = msg  # Store as a string
        print("Received transport info:", received_transport_info)
    except ValueError:
        print("Received non-numeric transport time, ignoring.")