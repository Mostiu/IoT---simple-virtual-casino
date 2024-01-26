import paho.mqtt.client as mqtt
import time


def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")


def on_message(client, userdata, msg):
    print(f"Received response: {msg.payload.decode()}")


def on_publish(client, userdata, mid):
    print(f"Message Published with MID: {mid}")


def on_disconnect(client, userdata, rc):
    print(f"Disconnected with result code {rc}")


# Change these values based on your MQTT broker configuration
broker_address = "localhost"
broker_port = 1883

client_id = "client_1"  # Unique client ID for each client
topic = "your_topic"

client = mqtt.Client(client_id)
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish
client.on_disconnect = on_disconnect

client.connect(broker_address, broker_port, 60)

try:
    client.loop_start()

    while True:
        client_id = input("Enter client ID: ")
        bet_size = input("Enter bet size: ")
        color = input("Enter color (e.g., red, black): ")
        client.subscribe(f"{client_id}_response")

        message = f"{client_id},{bet_size}, {color}"

        client.publish(topic, message)

        time.sleep(1)

except KeyboardInterrupt:
    print("Client shutting down")

finally:
    client.loop_stop()
    client.disconnect()
