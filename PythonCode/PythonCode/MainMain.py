# main.py
import time
import machine
import bme280
from neopixel import NeoPixel  # Library for controlling the RGB LED
import sh1106  # Using the SH1106 driver for your OLED
import mqtt_connection  # Import the MQTT connection module

# --- SPI SETUP for the MCP3008 ADC ---
spi = machine.SPI(
    1,  # Using HSPI
    baudrate=1_000_000,
    polarity=0,
    phase=0,
    sck=machine.Pin(6),  # SPI clock
    mosi=machine.Pin(5),  # Master-Out Slave-In
    miso=machine.Pin(7)   # Master-In Slave-Out
)
cs = machine.Pin(4, machine.Pin.OUT)
cs.value(1)  # Deselect the MCP3008

# --- Buzzer (Active Speaker) SETUP ---
buzzer_pin = machine.Pin(21, machine.Pin.OUT)
buzzer = machine.PWM(buzzer_pin)
buzzer.duty(0)

def beep(frequency=2000, duration=0.1):
    """
    Plays a beep sound at the given frequency and duration.
    """
    buzzer.freq(frequency)
    buzzer.duty(512)  # 50% duty cycle
    time.sleep(duration)
    buzzer.duty(0)    # Turn off the buzzer

def read_mcp3008(channel):
    """
    Reads the MCP3008 ADC on the specified channel (0-7)
    and returns a 10-bit value.
    """
    buf = bytearray(3)
    buf[0] = 0x01  # Start bit
    buf[1] = (0x08 + channel) << 4  # Channel selection + config
    buf[2] = 0x00  # Placeholder

    cs.value(0)  # Select the MCP3008
    spi.write_readinto(buf, buf)
    cs.value(1)  # Deselect the MCP3008

    result = ((buf[1] & 0x03) << 8) | buf[2]
    return result

# --- I2C SETUP for the BME280 sensor ---
i2c = machine.I2C(0, sda=machine.Pin(2), scl=machine.Pin(3), freq=400000)
print("I2C scan:", i2c.scan())
bme = bme280.BME280(i2c=i2c)

# --- Display (SH1106) SETUP ---
display = sh1106.SH1106_I2C(128, 64, i2c, addr=0x3C)
display.fill(0)
display.show()

# --- RGB LED SETUP ---
led_pin = machine.Pin(8, machine.Pin.OUT)
led = NeoPixel(led_pin, 1)

def set_led_color(red, green, blue):
    led[0] = (red, green, blue)
    led.write()

# --- Motion Sensor SETUP ---
# Using a pull-up resistor; for this sensor active LOW means motion detected.
motion_sensor = machine.Pin(22, machine.Pin.IN, machine.Pin.PULL_UP)

# --- Variables for display update and motion control ---
display_state = 0  # 0: Temperature, 1: Humidity, 2: Pressure
last_display_update = time.ticks_ms()
last_motion_time = 0  # Timestamp of the last motion event
DISPLAY_TIMEOUT = 10000  # Display remains on for 10 seconds after motion stops (in ms)
THRESHOLD = 900  # ADC threshold for LED control


def update_display(message):
    display.fill(0)  # Clear display

    max_chars_per_line = 16  # Max characters per line (for 8x8 font)
    words = message.split()  # Split message into words
    lines = []
    current_line = ""

    # Build lines ensuring words are not cut
    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars_per_line:
            current_line += " " + word if current_line else word
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)  # Add last line

    # Ensure only 4 lines are displayed
    for i, line in enumerate(lines[:4]):
        text_width = len(line) * 8  # Width of the text in pixels
        x = (128 - text_width) // 2  # Centering formula
        y = i * 10  # Spacing between lines
        display.text(line, x, y)  # Draw centered text

    display.show()

def scroll_text(message, delay=0.1):
    """Scrolls long text horizontally while keeping words intact and centered vertically."""
    display.fill(0)

    max_width = 128  # OLED width in pixels
    max_chars = max_width // 8  # 16 chars per line (since font is 8x8 pixels)

    words = message.split()
    lines = []
    current_line = ""

    # Build lines ensuring words are not cut
    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars:
            current_line += " " + word if current_line else word
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)  # Add last line

    # If the message fits on screen, display it normally
    if len(lines) <= 4:
        update_display(message)
        return

    # Scroll effect if more than 4 lines
    y_position = (64 - 8) // 2  # Center vertically

    full_text = "  ".join(lines)  # Combine lines with space for smooth scrolling
    text_width = len(full_text) * 8  # Total width in pixels

    # Scroll text from right to left
    for offset in range(-max_width, text_width):
        display.fill(0)  # Clear screen
        display.text(full_text[max(0, offset//8):], -offset % text_width, y_position)
        display.show()
        time.sleep(delay)

# --- MQTT Setup ---
# Define your topics here in the main file.
#TOPIC_ADC    = b"home/esp32/adc"
TOPIC_TEMP   = b"home/esp32/temp"
TOPIC_HUM    = b"home/esp32/hum"
TOPIC_PRESS  = b"home/esp32/press"
TOPIC_STATUS = b"home/esp32/status"

# Connect to WiFi and MQTT broker
mqtt_connection.connect_wifi()
mqtt_client = mqtt_connection.mqtt_connect()

# Publish an initial status message
if mqtt_client:
    mqtt_connection.publish_data(mqtt_client, TOPIC_STATUS, b"ESP32 Test Online")
    mqtt_connection.mqtt_subscribe(mqtt_client)  # Pass functions


# Checks what the outside Temp is and give a Hint for the User
def process_received_temperature():
    temp = mqtt_connection.received_temperature
    if temp is not None:
        if temp > 25:
            return f"Outside Temperature: {temp}C It's sunny, take your sunglasses!"
        elif temp < 10:
            return f"Outside Temperature: {temp}C It's a cold day, wear a warm coat!"
        else:
            return f"It's {temp}C Outside, enjoy your day!"
    else:
        return "No temperature data received yet."


def process_received_transport_info():
    """Formats the next transport departure message."""
    transport_info = mqtt_connection.received_transport_info

    if transport_info is not None:
        return "Next Bus: " + transport_info
    else:
        return "No transport data received yet."



while True:
    current_time = time.ticks_ms()

    # Check for motion; if motion is detected, update last_motion_time.
    # With pull-up configuration, a value of 0 means motion.
    if motion_sensor.value() == 1:
        last_motion_time = current_time
        print("Motion detected!")

    # Read ADC values from MCP3008 (pressure sensors)
    adc0 = read_mcp3008(0)
    adc1 = read_mcp3008(1)
    adc2 = read_mcp3008(2)
    adc3 = read_mcp3008(3)
    print("ADC Values:", adc0, adc1, adc2, adc3)

    # Calculate LED color based on ADC readings
    red = 255 if (adc0 >= THRESHOLD or adc3 >= THRESHOLD) else 0
    green = 255 if (adc1 >= THRESHOLD or adc3 >= THRESHOLD) else 0
    blue = 255 if (adc2 >= THRESHOLD) else 0
    set_led_color(red, green, blue)

    # Check each pressure sensor and play a unique sound if triggered
    if adc0 >= THRESHOLD:
        beep(frequency=1000, duration=0.3)  # Sound for sensor 0
    if adc1 >= THRESHOLD:
        beep(frequency=1200, duration=0.3)  # Sound for sensor 1
    if adc2 >= THRESHOLD:
        beep(frequency=1400, duration=0.3)  # Sound for sensor 2
    if adc3 >= THRESHOLD:
        beep(frequency=1600, duration=0.3)  # Sound for sensor 3

    # Read sensor values from BME280 (temperature, pressure, humidity)
    sensor_values = bme.values
    # bme.values returns a tuple of strings: (temperature, pressure, humidity)
    temperature, pressure, humidity = sensor_values
    print("BME280 Values:", temperature, pressure, humidity)

    # Publish BME280 sensor data every second via MQTT
    if mqtt_client:
        mqtt_connection.publish_data(mqtt_client, TOPIC_TEMP, temperature.encode())
        mqtt_connection.publish_data(mqtt_client, TOPIC_HUM, humidity.encode())
        mqtt_connection.publish_data(mqtt_client, TOPIC_PRESS, pressure.encode())
        mqtt_connection.publish_data(mqtt_client, TOPIC_STATUS, b"Online")
        mqtt_client.check_msg()  # This checks for new messages

        # If desired, you could also publish ADC values:
        #mqtt_connection.publish_data(mqtt_client, TOPIC_ADC, str(adc0).encode())


    # Check if the display should remain on (i.e. if motion was detected within the last 10 seconds)
    if time.ticks_diff(current_time, last_motion_time) < DISPLAY_TIMEOUT:
        # Display is on: update the display every 3 seconds
        if time.ticks_diff(current_time, last_display_update) >= 5000:
            if display_state == 0:
                message = f"Inside Temperature: {temperature}"
            elif display_state == 1:
                message = "Inside Humidity: " + humidity
            elif display_state == 2:
                message = "Inside Pressure: " + pressure
            elif display_state == 3:
                message = process_received_temperature()
            elif display_state == 4:
                message = process_received_transport_info()

            if len(message) > 64:  # If too long, scroll it
                scroll_text(message)
            else:  # Otherwise, just display normally
                update_display(message)

            display_state = (display_state + 1) % 5
            last_display_update = current_time

    else:
        # No recent motion: clear the display (turn it off)
        display.fill(0)
        display.show()

    time.sleep(1)