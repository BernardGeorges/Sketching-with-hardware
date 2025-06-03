import network
import time
import ubinascii
import ujson
from umqtt.simple import MQTTClient

# Wi-Fi configuration
SSID = "Two Girls One Router"
PASSWORD = "Pommesgesichter"


MQTT_USER = "SmartCarpet"      # If needed
MQTT_PASS = "smartcarpet"

# MQTT configuration
MQTT_BROKER = "192.168.178.113"   # Replace with your broker's IP address or hostname
MQTT_PORT = 1883  # Default MQTT port
MQTT_TOPIC = b"home/esp/weather"  # The topic to subscribe to


# Connect to Wi-Fi
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(1)
    print("Connected to Wi-Fi:", wlan.ifconfig())
    return wlan


# Callback function when a message is received
def mqtt_callback(topic, msg):
    print("Message received on topic:", topic)
    try:
        data = ujson.loads(msg)
        event = data.get("event")
        if event is not None:
            print("Event:", event)
            if event == -1:
                print("BRRRR... TAKE A THICK JACK OUT")
                # Add your custom action here (e.g., toggle an LED, etc.)
    except Exception as e:
        print("Error decoding JSON:", e)


# Main function
def main():
    # Connect to Wi-Fi
    connect_wifi(SSID, PASSWORD)

    # Create a unique client ID based on the device MAC address
    client_id = "esp-id"

    # Initialize MQTT client and set callback
    client = MQTTClient(client_id, MQTT_BROKER, port=MQTT_PORT, user=MQTT_USER, password=MQTT_PASS)
    client.set_callback(mqtt_callback)

    # Connect to the MQTT broker
    print("Connecting to MQTT broker...")
    client.connect()
    print("Connected with client ID:", client_id)

    # Subscribe to the topic
    client.subscribe(MQTT_TOPIC)
    print("Subscribed to topic:", MQTT_TOPIC.decode())

    try:
        # Wait for messages indefinitely
        while True:
            client.wait_msg()  # This blocks until a message is received
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        client.disconnect()
        print("Disconnected from MQTT broker")


# Run the main function
if __name__ == "__main__":
    main()