import paho.mqtt.client as mqtt

class MQTTClientWrapper:
    def __init__(self, broker_ip, port, username, password, topic):
        self.mqtt_broker_ip = broker_ip
        self.mqtt_port = port
        self.mqtt_username = username
        self.mqtt_password = password
        self.mqtt_topic = topic

        self.client = mqtt.Client()
        self.client.username_pw_set(username=username, password=password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe(self.mqtt_topic)

    def on_message(self, client, userdata, msg):
        print(f"Received message on topic {msg.topic}: {msg.payload.decode()}")

    def connect(self):
        self.client.connect(self.mqtt_broker_ip, self.mqtt_port, 60)

    def start(self):
        self.client.loop_start()

    def run_forever(self):
        try:
            while True:
                pass
        except KeyboardInterrupt:
            # Gracefully exit on Ctrl+C
            print("Exiting the script.")
            self.client.disconnect()

if __name__ == "__main__":
    mqtt_broker_ip = "139.162.50.185"
    mqtt_port = 1883
    mqtt_username = "kapraadmin"
    mqtt_password = "kapraadmin"
    mqtt_topic = "esp/ds18b20/temperature1"

    mqtt_client = MQTTClientWrapper(mqtt_broker_ip, mqtt_port, mqtt_username, mqtt_password, mqtt_topic)
    mqtt_client.connect()
    mqtt_client.start()
    mqtt_client.run_forever()
