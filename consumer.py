# mqtt_consumer.py
import os
import django
import paho.mqtt.client as mqtt
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_monitor.settings')
django.setup()

from data_management.models import WardReading, Ward, PatientVitals, Patient

# Configuration - adjust these based on your setup
DEFAULT_WARD_ID = 1
DEFAULT_PATIENT_ID = 2

# MQTT Topics from Pico
TOPIC_TEMP_DHT = "ward/temperature_dht"
TOPIC_HUMID = "ward/humidity"
TOPIC_SPO2 = "ward/spo2"
TOPIC_HEART_RATE = "ward/heart_rate"
TOPIC_SOUND = "ward/sound"
TOPIC_LIGHT = "ward/light"
TOPIC_TEMP_LM35 = "ward/temperature_lm35"

# Cache to store sensor readings
sensor_cache = {
    "ward_temp_dht": None,
    "ward_temp_lm35": None,
    "ward_humidity": None,
    "ward_sound": None,
    "ward_light": None,
    "patient_spo2": None,
    "patient_heart_rate": None,
    "timestamp": None
}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✓ Connected to MQTT broker successfully")

        # Subscribe to all Pico topics
        topics = [
            TOPIC_TEMP_DHT,
            TOPIC_HUMID,
            TOPIC_SPO2,
            TOPIC_HEART_RATE,
            TOPIC_SOUND,
            TOPIC_LIGHT,
            TOPIC_TEMP_LM35
        ]

        for topic in topics:
            client.subscribe(topic)
            print(f"✓ Subscribed to: {topic}")

    else:
        print(f"Failed to connect to MQTT broker. Return code: {rc}")

def save_ward_reading():
    """Save a ward reading when we have sufficient ward sensor data"""
    try:
        # Use DHT temperature as primary, fall back to LM35 if needed
        ward_temp = sensor_cache["ward_temp_dht"] or sensor_cache["ward_temp_lm35"]

        if (ward_temp is not None and
            sensor_cache["ward_humidity"] is not None):

            ward = Ward.objects.get(id=DEFAULT_WARD_ID)

            WardReading.objects.create(
                ward=ward,
                temperature=ward_temp,
                humidity=sensor_cache["ward_humidity"],
                noise_level=sensor_cache["ward_sound"] or 0.0,  # Default to 0 if no sound data
                light_intensity=sensor_cache["ward_light"]
            )

            print(f"✅ Saved ward reading: T={ward_temp}°C, H={sensor_cache['ward_humidity']}%, Sound={sensor_cache['ward_sound']}, Light={sensor_cache['ward_light']}")

            # Reset ward cache after saving
            sensor_cache["ward_temp_dht"] = None
            sensor_cache["ward_temp_lm35"] = None
            sensor_cache["ward_humidity"] = None
            sensor_cache["ward_sound"] = None
            sensor_cache["ward_light"] = None

    except Ward.DoesNotExist:
        print(f"✗ Ward with ID {DEFAULT_WARD_ID} not found. Please create a ward in the admin panel.")
    except Exception as e:
        print(f"✗ Error saving ward reading: {e}")

def save_patient_vitals():
    """Save patient vitals when we have sufficient patient sensor data"""
    try:
        if (sensor_cache["patient_spo2"] is not None and
            sensor_cache["patient_heart_rate"] is not None):

            patient = Patient.objects.get(user_id=DEFAULT_PATIENT_ID)

            # Use ward temperature as patient temperature if available
            patient_temp = sensor_cache["ward_temp_dht"] or sensor_cache["ward_temp_lm35"] or 36.5  # Default body temp

            PatientVitals.objects.create(
                patient=patient,
                temperature=patient_temp,
                heart_rate=int(sensor_cache["patient_heart_rate"]),
                oxygen_saturation=sensor_cache["patient_spo2"]
            )

            print(f"✅ Saved patient vitals: T={patient_temp}°C, HR={sensor_cache['patient_heart_rate']}bpm, SpO2={sensor_cache['patient_spo2']}%")

            # Reset patient cache after saving
            sensor_cache["patient_spo2"] = None
            sensor_cache["patient_heart_rate"] = None

    except Patient.DoesNotExist:
        print(f"✗ Patient with user_id {DEFAULT_PATIENT_ID} not found. Please create a patient in the admin panel.")
    except Exception as e:
        print(f"✗ Error saving patient vitals: {e}")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"📡 Received: {topic} => {payload}")

    try:
        value = float(payload)
        sensor_cache["timestamp"] = datetime.now()

        # Process different sensor topics
        if topic == TOPIC_TEMP_DHT:
            sensor_cache["ward_temp_dht"] = value
            print(f"🌡️  DHT Temperature: {value}°C")

        elif topic == TOPIC_TEMP_LM35:
            sensor_cache["ward_temp_lm35"] = value
            print(f"🌡️  LM35 Temperature: {value}°C")

        elif topic == TOPIC_HUMID:
            sensor_cache["ward_humidity"] = value
            print(f"💧 Humidity: {value}%")

        elif topic == TOPIC_SOUND:
            sensor_cache["ward_sound"] = value
            print(f"🔊 Sound Level: {value} dB")

        elif topic == TOPIC_LIGHT:
            sensor_cache["ward_light"] = value
            print(f"💡 Light Intensity: {value}")

        elif topic == TOPIC_SPO2:
            sensor_cache["patient_spo2"] = value
            print(f"🫁 Blood Oxygen (SpO2): {value}%")

        elif topic == TOPIC_HEART_RATE:
            sensor_cache["patient_heart_rate"] = value
            print(f"❤️  Heart Rate: {value} bpm")

        # Try to save complete readings
        save_ward_reading()
        save_patient_vitals()

    except ValueError:
        print(f"✗ Invalid data received from {topic}: {payload}")
    except Exception as e:
        print(f"✗ Error processing message from {topic}: {e}")

def print_startup_info():
    """Print startup information and configuration"""
    print("=" * 60)
    print("🏥 HEALTH MONITOR MQTT CONSUMER")
    print("=" * 60)
    print(f"📡 Connecting to MQTT broker at 127.0.0.1:1883")
    print(f"🏥 Ward readings will be saved to Ward ID: {DEFAULT_WARD_ID}")
    print(f"🩺 Patient vitals will be saved to Patient ID: {DEFAULT_PATIENT_ID}")
    print()
    print("📋 Monitoring Topics:")
    print(f"   🌡️  DHT Temperature: {TOPIC_TEMP_DHT}")
    print(f"   🌡️  LM35 Temperature: {TOPIC_TEMP_LM35}")
    print(f"   💧 Humidity: {TOPIC_HUMID}")
    print(f"   🔊 Sound Level: {TOPIC_SOUND}")
    print(f"   💡 Light Intensity: {TOPIC_LIGHT}")
    print(f"   🫁 Blood Oxygen (SpO2): {TOPIC_SPO2}")
    print(f"   ❤️  Heart Rate: {TOPIC_HEART_RATE}")
    print()
    print("📊 Data Storage:")
    print("   • Ward environmental data → WardReading model")
    print("   • Patient vital signs → PatientVitals model")
    print()
    print("🚀 Starting MQTT listener... (Press Ctrl+C to stop)")
    print("=" * 60)

def main():
    print_startup_info()

    try:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message

        # Connect to local MQTT broker (Mosquitto)
        client.connect("127.0.0.1", 1883, 60)

        print("🔄 Starting MQTT loop...")
        client.loop_forever()

    except KeyboardInterrupt:
        print("\n⏹️  Stopping MQTT consumer...")
        client.disconnect()
        print("✅ Disconnected successfully")
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("💡 Make sure your MQTT broker (Mosquitto) is running on 127.0.0.1:1883")
        print("💡 You can start it with: sudo systemctl start mosquitto")

if __name__ == "__main__":
    main()
