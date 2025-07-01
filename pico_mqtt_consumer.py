#!/usr/bin/env python3
"""
Health Monitor - Pico MQTT Consumer with CSV Logging

This script listens to all MQTT topics from the Raspberry Pi Pico and processes:
1. Ward environmental data: DHT temperature, LM35 temperature, humidity, sound, light
2. Patient vital signs: heart rate, SpO2 (blood oxygen saturation)

The data is saved to:
- Django database (WardReading and PatientVitals models)
- CSV files for backup/analysis
- Real-time console logging with emojis

MQTT Topics monitored:
- ward/temperature_dht (DHT22 temperature sensor)
- ward/temperature_lm35 (LM35 temperature sensor)
- ward/humidity (DHT22 humidity sensor)
- ward/sound (sound level sensor)
- ward/light (light intensity sensor)
- ward/spo2 (pulse oximeter SpO2)
- ward/heart_rate (pulse oximeter heart rate)
"""

import os
import django
import csv
import paho.mqtt.client as mqtt
from datetime import datetime
from pathlib import Path

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_monitor.settings')
django.setup()

from data_management.models import WardReading, Ward, PatientVitals, Patient

# Configuration
DEFAULT_WARD_ID = 1
DEFAULT_PATIENT_ID = 2

# MQTT Topics from Pico
TOPICS = {
    "ward/temperature_dht": "ward_temp_dht",
    "ward/temperature_lm35": "ward_temp_lm35",
    "ward/humidity": "ward_humidity",
    "ward/sound": "ward_sound",
    "ward/light": "ward_light",
    "ward/spo2": "patient_spo2",
    "ward/heart_rate": "patient_heart_rate"
}

# CSV file configuration
CSV_DIR = Path("sensor_logs")
CSV_DIR.mkdir(exist_ok=True)

WARD_CSV = CSV_DIR / "ward_readings.csv"
PATIENT_CSV = CSV_DIR / "patient_vitals.csv"
RAW_CSV = CSV_DIR / "raw_sensor_data.csv"

# CSV Headers
WARD_HEADERS = ["timestamp", "dht_temp", "lm35_temp", "humidity", "sound_level", "light_intensity"]
PATIENT_HEADERS = ["timestamp", "temperature", "heart_rate", "spo2"]
RAW_HEADERS = ["timestamp", "topic", "value"]

# Initialize CSV files with headers if they don't exist
def init_csv_files():
    """Initialize CSV files with headers if they don't exist"""
    for csv_file, headers in [(WARD_CSV, WARD_HEADERS), (PATIENT_CSV, PATIENT_HEADERS), (RAW_CSV, RAW_HEADERS)]:
        if not csv_file.exists():
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            print(f"📄 Created CSV file: {csv_file}")

# Sensor data cache
sensor_cache = {
    "ward_temp_dht": None,
    "ward_temp_lm35": None,
    "ward_humidity": None,
    "ward_sound": None,
    "ward_light": None,
    "patient_spo2": None,
    "patient_heart_rate": None,
    "last_ward_save": None,
    "last_patient_save": None
}

def log_to_raw_csv(topic, value):
    """Log all raw sensor data to CSV"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(RAW_CSV, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, topic, value])
    except Exception as e:
        print(f"✗ Error writing to raw CSV: {e}")

def log_ward_to_csv():
    """Log ward reading to CSV"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(WARD_CSV, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                sensor_cache["ward_temp_dht"],
                sensor_cache["ward_temp_lm35"],
                sensor_cache["ward_humidity"],
                sensor_cache["ward_sound"],
                sensor_cache["ward_light"]
            ])
        print(f"📄 Logged ward data to CSV")
    except Exception as e:
        print(f"✗ Error writing ward data to CSV: {e}")

def log_patient_to_csv():
    """Log patient vitals to CSV"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Use available temperature sensor data
        temp = sensor_cache["ward_temp_dht"] or sensor_cache["ward_temp_lm35"] or 36.5

        with open(PATIENT_CSV, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                temp,
                sensor_cache["patient_heart_rate"],
                sensor_cache["patient_spo2"]
            ])
        print(f"📄 Logged patient vitals to CSV")
    except Exception as e:
        print(f"✗ Error writing patient data to CSV: {e}")

def save_ward_reading():
    """Save ward reading to database when we have sufficient environmental data"""
    try:
        # Require at least temperature and humidity
        ward_temp = sensor_cache["ward_temp_dht"] or sensor_cache["ward_temp_lm35"]

        if ward_temp is not None and sensor_cache["ward_humidity"] is not None:
            ward = Ward.objects.get(id=DEFAULT_WARD_ID)

            reading = WardReading.objects.create(
                ward=ward,
                temperature=ward_temp,
                humidity=sensor_cache["ward_humidity"],
                noise_level=sensor_cache["ward_sound"] or 0.0,
                light_intensity=sensor_cache["ward_light"]
            )

            print(f"💾 Saved ward reading #{reading.id}: T={ward_temp}°C, H={sensor_cache['ward_humidity']}%, Sound={sensor_cache['ward_sound']}, Light={sensor_cache['ward_light']}")

            # Log to CSV
            log_ward_to_csv()

            # Reset environmental cache after saving
            sensor_cache["ward_temp_dht"] = None
            sensor_cache["ward_temp_lm35"] = None
            sensor_cache["ward_humidity"] = None
            sensor_cache["ward_sound"] = None
            sensor_cache["ward_light"] = None
            sensor_cache["last_ward_save"] = datetime.now()

    except Ward.DoesNotExist:
        print(f"✗ Ward with ID {DEFAULT_WARD_ID} not found. Please create a ward in the admin panel.")
    except Exception as e:
        print(f"✗ Error saving ward reading: {e}")

def save_patient_vitals():
    """Save patient vitals to database when we have vital signs data"""
    try:
        if (sensor_cache["patient_spo2"] is not None and
            sensor_cache["patient_heart_rate"] is not None):

            patient = Patient.objects.get(user_id=DEFAULT_PATIENT_ID)

            # Use most recent temperature reading
            patient_temp = sensor_cache["ward_temp_dht"] or sensor_cache["ward_temp_lm35"] or 36.5

            vitals = PatientVitals.objects.create(
                patient=patient,
                temperature=patient_temp,
                heart_rate=int(sensor_cache["patient_heart_rate"]),
                oxygen_saturation=sensor_cache["patient_spo2"]
            )

            print(f"💾 Saved patient vitals #{vitals.id}: T={patient_temp}°C, HR={sensor_cache['patient_heart_rate']}bpm, SpO2={sensor_cache['patient_spo2']}%")

            # Log to CSV
            log_patient_to_csv()

            # Reset patient cache after saving
            sensor_cache["patient_spo2"] = None
            sensor_cache["patient_heart_rate"] = None
            sensor_cache["last_patient_save"] = datetime.now()

    except Patient.DoesNotExist:
        print(f"✗ Patient with user_id {DEFAULT_PATIENT_ID} not found. Please create a patient in the admin panel.")
    except Exception as e:
        print(f"✗ Error saving patient vitals: {e}")

def get_sensor_emoji(topic):
    """Get appropriate emoji for sensor type"""
    emoji_map = {
        "ward/temperature_dht": "🌡️",
        "ward/temperature_lm35": "🌡️",
        "ward/humidity": "💧",
        "ward/sound": "🔊",
        "ward/light": "💡",
        "ward/spo2": "🫁",
        "ward/heart_rate": "❤️"
    }
    return emoji_map.get(topic, "📊")

def get_sensor_unit(topic):
    """Get appropriate unit for sensor type"""
    unit_map = {
        "ward/temperature_dht": "°C",
        "ward/temperature_lm35": "°C",
        "ward/humidity": "%",
        "ward/sound": "dB",
        "ward/light": "lux",
        "ward/spo2": "%",
        "ward/heart_rate": "bpm"
    }
    return unit_map.get(topic, "")

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the MQTT broker"""
    if rc == 0:
        print("✅ Connected to MQTT broker successfully")

        # Subscribe to all Pico topics
        for topic in TOPICS.keys():
            result = client.subscribe(topic)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                print(f"✅ Subscribed to: {topic}")
            else:
                print(f"✗ Failed to subscribe to: {topic}")

        print(f"📡 Monitoring {len(TOPICS)} sensor topics...")

    else:
        print(f"✗ Failed to connect to MQTT broker. Return code: {rc}")

def on_disconnect(client, userdata, rc):
    """Callback for when the client disconnects from the MQTT broker"""
    if rc != 0:
        print("⚠️  Unexpected disconnection from MQTT broker")
    else:
        print("✅ Gracefully disconnected from MQTT broker")

def on_message(client, userdata, msg):
    """Callback for when a message is received from the MQTT broker"""
    topic = msg.topic
    payload = msg.payload.decode().strip()

    emoji = get_sensor_emoji(topic)
    unit = get_sensor_unit(topic)

    print(f"📡 {emoji} {topic}: {payload}{unit}")

    try:
        value = float(payload)

        # Log all data to raw CSV
        log_to_raw_csv(topic, value)

        # Update sensor cache
        if topic in TOPICS:
            cache_key = TOPICS[topic]
            sensor_cache[cache_key] = value

            # Print formatted sensor reading
            sensor_name = cache_key.replace('_', ' ').title()
            print(f"   💾 Cached: {sensor_name} = {value}{unit}")

        # Attempt to save complete readings
        save_ward_reading()
        save_patient_vitals()

    except ValueError:
        print(f"✗ Invalid numeric data from {topic}: '{payload}'")
    except Exception as e:
        print(f"✗ Error processing message from {topic}: {e}")

def print_cache_status():
    """Print current cache status for debugging"""
    print("\n📊 Current Sensor Cache:")
    print("-" * 40)
    for key, value in sensor_cache.items():
        if not key.startswith('last_'):
            status = f"{value}" if value is not None else "None"
            print(f"   {key.replace('_', ' ').title()}: {status}")
    print("-" * 40)

def print_startup_banner():
    """Print startup banner with configuration info"""
    print("=" * 70)
    print("🏥 HEALTH MONITOR - PICO MQTT CONSUMER")
    print("=" * 70)
    print(f"🚀 Starting comprehensive sensor monitoring system")
    print(f"📡 MQTT Broker: 127.0.0.1:1883")
    print(f"🏥 Ward ID: {DEFAULT_WARD_ID}")
    print(f"🩺 Patient ID: {DEFAULT_PATIENT_ID}")
    print()
    print("📋 Sensor Topics:")
    for topic in TOPICS.keys():
        emoji = get_sensor_emoji(topic)
        print(f"   {emoji} {topic}")
    print()
    print("💾 Data Storage:")
    print(f"   📊 Database: WardReading & PatientVitals models")
    print(f"   📄 Ward CSV: {WARD_CSV}")
    print(f"   📄 Patient CSV: {PATIENT_CSV}")
    print(f"   📄 Raw Data CSV: {RAW_CSV}")
    print()
    print("🔧 Features:")
    print("   • Real-time sensor monitoring with emojis")
    print("   • Automatic database saves when data is complete")
    print("   • CSV logging for all sensor data")
    print("   • Smart caching system")
    print("   • Error handling and recovery")
    print()
    print("⌨️  Press Ctrl+C to stop monitoring")
    print("=" * 70)

def print_shutdown_stats():
    """Print shutdown statistics"""
    print("\n📊 Session Statistics:")
    print("-" * 40)
    last_ward = sensor_cache.get("last_ward_save")
    last_patient = sensor_cache.get("last_patient_save")

    if last_ward:
        print(f"   Last Ward Save: {last_ward.strftime('%H:%M:%S')}")
    else:
        print("   Last Ward Save: None")

    if last_patient:
        print(f"   Last Patient Save: {last_patient.strftime('%H:%M:%S')}")
    else:
        print("   Last Patient Save: None")
    print("-" * 40)

def main():
    """Main function to run the MQTT consumer"""
    print_startup_banner()

    # Initialize CSV files
    init_csv_files()

    try:
        # Create MQTT client
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message

        # Connect to MQTT broker
        print("🔌 Connecting to MQTT broker...")
        client.connect("127.0.0.1", 1883, 60)

        # Start the MQTT loop
        print("🔄 Starting MQTT message loop...")
        client.loop_forever()

    except KeyboardInterrupt:
        print("\n⏹️  Shutting down MQTT consumer...")
        print_cache_status()
        print_shutdown_stats()
        client.disconnect()
        print("✅ Health Monitor MQTT Consumer stopped successfully")

    except ConnectionRefusedError:
        print("❌ Connection refused! MQTT broker is not running.")
        print("💡 Start Mosquitto with: sudo systemctl start mosquitto")
        print("💡 Or install it with: sudo apt install mosquitto mosquitto-clients")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("💡 Make sure:")
        print("   - MQTT broker (Mosquitto) is running on 127.0.0.1:1883")
        print("   - Django database is properly configured")
        print("   - Required Ward and Patient records exist")

if __name__ == "__main__":
    main()
