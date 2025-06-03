import machine
import time
import bme280
from neopixel import NeoPixel  # Import der Bibliothek zur Ansteuerung der RGB-LED

# --- SPI-SETUP für den MCP3008 ADC ---
# Initialisierung der SPI-Schnittstelle, hier wird HSPI verwendet.
spi = machine.SPI(
    1,  # Auswahl des SPI-Peripheriegeräts (z. B. HSPI)
    baudrate=1_000_000,  # Kommunikationsgeschwindigkeit
    polarity=0,  # SPI-Polarity (Ruhezustand des Taktsignals)
    phase=0,  # SPI-Phase (Abtastzeitpunkt)
    sck=machine.Pin(6),  # Pin für den SPI-Takt
    mosi=machine.Pin(5),  # Pin für Master-Out Slave-In
    miso=machine.Pin(7)  # Pin für Master-In Slave-Out
)
# Initialisierung des Chip-Select-Pins (CS) für den MCP3008
cs = machine.Pin(4, machine.Pin.OUT)
cs.value(1)  # CS auf "High" setzen, um das Gerät nicht anzusprechen


def read_mcp3008(channel):
    """
    Liest den MCP3008 am angegebenen Kanal (0-7) und gibt einen 10-Bit-ADC-Wert zurück.
    """
    buf = bytearray(3)  # Erzeugt ein Bytearray für den SPI-Datenaustausch (3 Bytes)
    buf[0] = 0x01  # Startbit für die Kommunikation
    buf[1] = (0x08 + channel) << 4  # Kanalwahl + Konfiguration, nach links verschoben
    buf[2] = 0x00  # Drittes Byte wird als Platzhalter genutzt

    cs.value(0)  # Aktiviert den Chip-Select (CS wird Low gesetzt)
    spi.write_readinto(buf, buf)  # Senden und Empfangen der Daten über SPI
    cs.value(1)  # Deaktiviert den Chip-Select (CS wird wieder High gesetzt)

    # Das 10-Bit-Ergebnis wird aus den unteren 2 Bits von buf[1] und dem gesamten buf[2] zusammengesetzt
    result = ((buf[1] & 0x03) << 8) | buf[2]
    return result


# --- I2C-SETUP für den BME280 Sensor ---
# Initialisierung der I2C-Schnittstelle mit definierten SDA- und SCL-Pins
i2c = machine.I2C(0, sda=machine.Pin(2), scl=machine.Pin(3), freq=400000)
# Initialisierung des BME280 Sensors über I2C
bme = bme280.BME280(i2c=i2c)


def read_temp_humidity():
    """
    Liest Temperatur und Luftfeuchtigkeit vom BME280 Sensor aus und gibt diese aus.
    """
    # bme.values liefert typischerweise eine Tuple mit Temperatur, Druck und Luftfeuchtigkeit als Strings
    print("Temperatur/Luftfeuchtigkeit:", bme.values)


# --- RGB-LED SETUP ---
# Konfiguration des Pins, der die RGB-LED steuert (hier GPIO8)
led_pin = machine.Pin(8, machine.Pin.OUT)
# Initialisiert eine NeoPixel-Instanz mit einer LED
led = NeoPixel(led_pin, 1)


def set_led_color(red, green, blue):
    """
    Setzt die Farbe der RGB-LED.

    Parameter:
    red   -- Rotanteil (0-255)
    green -- Grünanteil (0-255)
    blue  -- Blauanteil (0-255)
    """
    led[0] = (red, green, blue)  # Weist der LED den Farbwert zu
    led.write()  # Überträgt den Wert an die LED


# --- HAUPTSCHLEIFE ---
THRESHOLD = 900  # Schwellenwert für die ADC-Werte, ab dem die LED auf volle Helligkeit geht

while True:
    # Einlesen der ADC-Werte von vier Kanälen des MCP3008
    adc0 = read_mcp3008(0)  # Drucksensor #1
    adc1 = read_mcp3008(1)  # Drucksensor #2
    adc2 = read_mcp3008(2)  # Drucksensor #3
    adc3 = read_mcp3008(3)  # Drucksensor #4
    print("ADC-Werte:", adc0, adc1, adc2, adc3)

    # Berechnung der Farbwerte basierend auf den ADC-Messwerten:
    # Wenn adc0 oder adc3 den Schwellenwert überschreiten, wird Rot aktiviert.
    red = 255 if (adc0 >= THRESHOLD or adc3 >= THRESHOLD) else 0
    # Wenn adc1 oder adc3 den Schwellenwert überschreiten, wird Grün aktiviert.
    green = 255 if (adc1 >= THRESHOLD or adc3 >= THRESHOLD) else 0
    # Wenn adc2 den Schwellenwert überschreitet, wird Blau aktiviert.
    blue = 255 if (adc2 >= THRESHOLD) else 0

    print("Berechnete Farbwerte - R: {}, G: {}, B: {}".format(red, green, blue))

    # Setzt die berechneten Farbwerte an der RGB-LED
    set_led_color(red, green, blue)

    # Liest Temperatur und Luftfeuchtigkeit vom BME280 Sensor aus
    read_temp_humidity()

    time.sleep(1)  # Kurze Pause von 1 Sekunde, bevor der nächste Messzyklus beginnt