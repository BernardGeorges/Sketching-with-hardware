import machine
import time
import bme280
from neopixel import NeoPixel  # Library for controlling the RGB LED
import sh1106  # Using the SH1106 driver for your OLED

# --- SPI SETUP for the MCP3008 ADC ---
spi = machine.SPI(
    1,  # Using HSPI
    baudrate=1_000_000,
    polarity=0,
    phase=0,
    sck=machine.Pin(6),  # SPI clock
    mosi=machine.Pin(5),  # Master-Out Slave-In
    miso=machine.Pin(7)  # Master-In Slave-Out
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


# --- Helper function to update the display ---
def update_display(message):
    display.fill(0)
    # Center the text (assuming an 8x8 pixel font)
    x = (128 - len(message) * 8) // 2
    y = (64 - 8) // 2
    display.text(message, x, y)
    display.show()


# --- Variables for display update and motion control ---
display_state = 0  # 0: Temperature, 1: Humidity, 2: Pressure
last_display_update = time.ticks_ms()
last_motion_time = 0  # Timestamp of the last motion event
DISPLAY_TIMEOUT = 10000  # Display remains on for 10 seconds after motion stops (in ms)
THRESHOLD = 900  # ADC threshold for LED control

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
    print("ADC-Werte:", adc0, adc1, adc2, adc3)



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
    print("BME280 Sensorwerte:", sensor_values)

    # Check if the display should remain on (i.e. if motion was detected within the last 10 seconds)
    if time.ticks_diff(current_time, last_motion_time) < DISPLAY_TIMEOUT:
        # Display is on: update the display every 3 seconds
        if time.ticks_diff(current_time, last_display_update) >= 3000:
            if display_state == 0:
                message = sensor_values[0]
            elif display_state == 1:
                message = sensor_values[2]
            elif display_state == 2:
                message = sensor_values[1]
            update_display(message)
            display_state = (display_state + 1) % 3
            last_display_update = current_time
    else:
        # No recent motion: clear the display (turn it off)
        display.fill(0)
        display.show()

    time.sleep(1)