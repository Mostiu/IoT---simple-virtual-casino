import paho.mqtt.client as mqtt
import time
from mfrc522 import MFRC522

class InteractiveMQTTClient:
    def __init__(self, broker_address, broker_port, client_id):
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.client_id = client_id

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_disconnect = self.on_disconnect

        self.client.message_callback_add(f"{self.client_id}_history_response", self.on_history)
        self.client.message_callback_add(f"{self.client_id}_response", self.on_game)

        self.client.user_data_set({"client_id": self.client_id})

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")

    def on_history(self, client, userdata, msg):
        print(f"Received history response: {msg.payload.decode()}")

    def on_game(self, client, userdata, msg):
        print(f"Received game response: {msg.payload.decode()}")

    def on_publish(self, client, userdata, mid):
        print(f"Message Published with MID: {mid}")

    def on_disconnect(self, client, userdata, rc):
        print(f"Disconnected with result code {rc}")

    def connect_to_broker(self):
        self.client.connect(self.broker_address, self.broker_port, 60)

    def read_rfid_card(self):
        MIFAREReader = MFRC522()

        time.sleep(2)

        while True:
            (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
            if status == MIFAREReader.MI_OK:
                (status, uid) = MIFAREReader.MFRC522_Anticoll()
                if status == MIFAREReader.MI_OK:
                    num = 0
                    for i in range(0, len(uid)):
                        num += uid[i] << (i * 8)
                    return str(num)

    def start(self):
        self.client.loop_start()
        self.client.subscribe(f"{self.client_id}_history_response")
        self.client.subscribe(f"{self.client_id}_response")

        try:
            while True:
                choice = input("Enter 'history' or 'game' to choose the type of message (or 'exit' to quit): ")

                if choice.lower() == 'exit':
                    break

                if choice.lower() not in ['history', 'game']:
                    print("Invalid choice. Please enter 'history', 'game', or 'exit'.")
                    continue

                player_id = self.read_rfid_card()
               # player_id = input("Enter player ID: ")

                if choice.lower() == 'history':
                    message = f"{self.client_id},{player_id}"
                    self.publish_message(choice, message)
                elif choice.lower() == 'game':
                    bet_size = input("Enter bet size: ")
                    color = input("Enter color (e.g., red, black): ")
                    message = f"{self.client_id},{bet_size},{color},{player_id}"
                    self.publish_message(choice, message)

                time.sleep(1)

        except KeyboardInterrupt:
            print("Client shutting down")

        finally:
            self.client.loop_stop()
            self.client.disconnect()

    def publish_message(self, topic, message):
        self.client.publish(topic, message)


if __name__ == "__main__":
    broker_address = "192.168.31.169"
    broker_port = 1883
    client_id = "client1"

    interactive_client = InteractiveMQTTClient(broker_address, broker_port, client_id)
    interactive_client.connect_to_broker()
    interactive_client.start()
