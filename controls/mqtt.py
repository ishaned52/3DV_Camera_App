import paho.mqtt.client as mqtt

class MQTTListener:
    def __init__(self):
        self.broker_ip = "139.162.50.185"
        self.port = 1883
        self.username = "kapraadmin"
        self.password = "kapraadmin"
        self.topic = "esp/ds18b20/temperature"
        self.client = mqtt.Client()
        self.client.username_pw_set(username=self.username, password=self.password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        print(f"Received message on topic {msg.topic}: {msg.payload.decode()}")

    def connect_and_listen(self):
        self.client.connect(self.broker_ip, self.port, 60)
        self.client.loop_start()

    def run(self):
        try:
            self.connect_and_listen()
            while True:
                pass
        except KeyboardInterrupt:
            # Gracefully exit on Ctrl+C
            print("Exiting the script.")
            self.client.disconnect()

