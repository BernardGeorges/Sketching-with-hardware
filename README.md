# Sketching-with-hardware
Project created for the course sketching with hardware. This project uses rasberryPI and some of its hardwares

The Smart Carpet integrates pressure sensors into a doormat, enabling secure, gesture-based inputs (e.g., step patterns functioning like a PIN code). Its discreet design ensures that the sensors remain hidden, providing an additional layer of security through security by obscurity.

All data is transmitted via analog signals to a central unit located inside the home, minimizing the risk of remote interception. The system is not directly connected to the internet, instead relying on the existing smart home network (e.g., Home Assistant) for secure operation.

In addition to security functions, the Smart Carpet can detect movement patterns, identify users, and trigger automated routines such as personalized greetings, indoor notifications, or package delivery alerts.

🛠️ Hardware Used
Component	Description
ESP32-C6-Dev	Wi-Fi + BLE controller board for managing sensor input and display output
1.3" OLED Display (B/W)	Small screen for showing real-time contextual data (weather, transit, etc.)
FSR03DE Pressure Sensors (x4)	Pressure-sensitive resistors arranged in a 2×2 matrix within the doormat
PIR Motion Sensor	Renkforce 1362990 – 360° motion detection to activate the display
Environmental Sensors	Measures temperature, humidity, and atmospheric pressure
Loudspeaker	Provides acoustic feedback (e.g., tone feedback for step patterns)
Raspberry Pi 5	Runs Home Assistant, connects via MQTT for data handling & automation


