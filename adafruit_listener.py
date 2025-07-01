"""
Health Monitor - Adafruit IO MQTT Listener

This script listens to multiple MQTT feeds from Adafruit IO and processes:
1. Ward environmental data: temperature, humidity, light intensity
2. Patient vital signs: temperature (heart rate and oxygen saturation from other sensors)

The data is saved to:
- Django database (WardReading and PatientVitals models)
- CSV file for backup/analysis

Feeds monitored:
- Ward temperature
- Ward humidity
- Light intensity
- Patient temperature
"""

import os
import django
import csv
from paho.mqtt.client import Client
import app_secrets

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_monitor.settings')
django.setup()

from data_management.models import WardReading, Ward, Microcontroller, PatientVitals, Patient

# Adafruit IO Credentials
AIO_USERNAME = app_secrets.AIO_USER
AIO_KEY = app_secrets.AIO_KEY
WARD_TEMP_FEED = app_secrets.WARD_TEMP_FEED
WARD_HUMIDITY_FEED = app_secrets.WARD_HUMIDITY_FEED
PATIENT_TEMPERATURE_FEED = app_secrets.PATIENT_TEMPERATURE_FEED
LIGHT_INTENSITY_FEED = app_secrets.LIGHT_INTENSITY_FEED

# Configuration constants
MICROCONTROLLER_IDENTIFIER = "raspberry-pi-pico-wh"
WARD_ID = 1
PATIENT_ID = 2
DEFAULT_HEART_RATE = 70
DEFAULT_OXYGEN_SATURATION = 98.0
DEFAULT_NOISE_LEVEL = 0.0

CSV_FILE_PATH = "sensor_data.csv"

# Make sure the CSV has headers
if not os.path.exists(CSV_FILE_PATH):
    with open(CSV_FILE_PATH, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["ward_temperature", "ward_humidity", "patient_temperature", "light_intensity", "timestamp"])

# Cache last known values for ward and patient data
sensor_cache = {
    "ward_temperature": None,
    "ward_humidity": None,
    "patient_temperature": None,
    "light_intensity": None
}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✓ Connected to Adafruit IO successfully")
        client.subscribe(WARD_TEMP_FEED)
        client.subscribe(WARD_HUMIDITY_FEED)
        client.subscribe(PATIENT_TEMPERATURE_FEED)
        client.subscribe(LIGHT_INTENSITY_FEED)
        print("✓ Subscribed to all feeds")
    else:
        print(f"✗ Failed to connect to Adafruit IO. Return code: {rc}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("✗ Unexpected disconnection from Adafruit IO")
    else:
        print("✓ Disconnected from Adafruit IO")

def on_message(client, userdata, msg):
    from datetime import datetime
    print(f" Received from {msg.topic}: {msg.payload.decode()}")

    try:
        value = float(msg.payload.decode())

        # Update sensor cache based on topic
        if msg.topic == WARD_TEMP_FEED:
            sensor_cache["ward_temperature"] = value
            print(f"  Ward temperature: {value}°C")
        elif msg.topic == WARD_HUMIDITY_FEED:
            sensor_cache["ward_humidity"] = value
            print(f" Ward humidity: {value}%")
        elif msg.topic == PATIENT_TEMPERATURE_FEED:
            sensor_cache["patient_temperature"] = value
            print(f" Patient temperature: {value}°C")
        elif msg.topic == LIGHT_INTENSITY_FEED:
            sensor_cache["light_intensity"] = value
            print(f" Light intensity: {value}")

        # Save ward readings if we have ward temperature, humidity, and light intensity
        if (sensor_cache["ward_temperature"] is not None and
            sensor_cache["ward_humidity"] is not None and
            sensor_cache["light_intensity"] is not None):

            try:
                ward = Ward.objects.get(id=WARD_ID)

                WardReading.objects.create(
                    ward=ward,
                    temperature=sensor_cache["ward_temperature"],
                    humidity=sensor_cache["ward_humidity"],
                    noise_level=DEFAULT_NOISE_LEVEL,  # Default value, can be updated when noise sensor is added
                    light_intensity=sensor_cache["light_intensity"]
                )

                print(f"Saved ward reading: T={sensor_cache['ward_temperature']}°C, H={sensor_cache['ward_humidity']}%, L={sensor_cache['light_intensity']}")

                # Reset ward-related cache
                sensor_cache["ward_temperature"] = None
                sensor_cache["ward_humidity"] = None
                sensor_cache["light_intensity"] = None

            except Ward.DoesNotExist:
                print(f"✗ Ward with ID {WARD_ID} not found")
            except Exception as e:
                print(f"✗ Error saving ward reading: {e}")

        # Save patient vitals if we have patient temperature
        if sensor_cache["patient_temperature"] is not None:
            try:
                patient = Patient.objects.get(user_id=PATIENT_ID)

                PatientVitals.objects.create(
                    patient=patient,
                    temperature=sensor_cache["patient_temperature"],
                    heart_rate=DEFAULT_HEART_RATE,  # Default value - should come from heart rate sensor
                    oxygen_saturation=DEFAULT_OXYGEN_SATURATION  # Default value - should come from pulse oximeter
                )

                print(f"✅ Saved patient vitals: T={sensor_cache['patient_temperature']}°C")

                # Reset patient cache
                sensor_cache["patient_temperature"] = None

            except Patient.DoesNotExist:
                print(f"✗ Patient with user_id {PATIENT_ID} not found")
            except Exception as e:
                print(f"✗ Error saving patient vitals: {e}")

        # Log to CSV with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(CSV_FILE_PATH, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    sensor_cache.get("ward_temperature", ""),
                    sensor_cache.get("ward_humidity", ""),
                    sensor_cache.get("patient_temperature", ""),
                    sensor_cache.get("light_intensity", ""),
                    timestamp
                ])
        except Exception as e:
            print(f"✗ Error writing to CSV: {e}")

    except ValueError:
        print(f"✗ Invalid data received: {msg.payload.decode()}")
    except Exception as e:
        print(f"✗ Error processing message: {e}")

# Setup MQTT client
client = Client()
client.username_pw_set(AIO_USERNAME, AIO_KEY)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

print("Starting Health Monitor MQTT Listener...")
print(f" Monitoring feeds:")
print(f"   - Ward Temperature: {WARD_TEMP_FEED}")
print(f"   - Ward Humidity: {WARD_HUMIDITY_FEED}")
print(f"   - Patient Temperature: {PATIENT_TEMPERATURE_FEED}")
print(f"   - Light Intensity: {LIGHT_INTENSITY_FEED}")
print(f"Data will be saved to database and {CSV_FILE_PATH}")

# Connect and listen
try:
    client.connect("io.adafruit.com", 1883, 60)
    print("Listening for sensor data... (Press Ctrl+C to stop)")
    client.loop_forever()
except KeyboardInterrupt:
    print("\nStopping listener...")
    client.disconnect()
    print("Disconnected successfully")
except Exception as e:
    print(f"Connection error: {e}")
