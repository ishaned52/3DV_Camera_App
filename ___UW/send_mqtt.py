import paho.mqtt.client as mqtt
import base64

# Define the MQTT parameters
mqtt_broker_ip = "139.162.50.185"
mqtt_port = 1883  # Default MQTT port
mqtt_username = "kapraadmin"
mqtt_password = "kapraadmin"
mqtt_topic = "esp/ds18b20/temperature1"

# Create an MQTT client
client = mqtt.Client()

# Set the username and password
client.username_pw_set(username=mqtt_username, password=mqtt_password)

# Connect to the MQTT broker
client.connect(mqtt_broker_ip, mqtt_port, 60)

# Message to send
binary_message = bytearray(b'\x01\x03\x01\xb4\xff\xb8\x02\x02\x01\x00\x05\x03\x04\x01\x00\x00\x05\r\x04\x02\x01\x01\x08\x01\x03\x06\xb4\xff\xbd\x02\x02\x06\x00\n\x03\x04\x06\x00\x00\x05\x12\x04\x02\x06\x01\r')
# Publish the message to the specified topic

base64_message = base64.b64encode(binary_message).decode()

print(base64_message)

client.publish(mqtt_topic, base64_message)

# Disconnect from the MQTT broker
client.disconnect()


# bytearray(b'\x01\x03\x01\xb4\xff\xb8\x02\x02\x01\x00\x05\x03\x04\x01\x00\x00\x05\r\x04\x02\x01\x01\x08\x01\x03\x06\xb4\xff\xbd\x02\x02\x06\x00\n\x03\x04\x06\x00\x00\x05\x12\x04\x02\x06\x01\r')