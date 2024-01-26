import paho.mqtt.client as mqtt
import threading

client_messages = {}

client_counter = 0

lock = threading.Lock()


def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("your_topic")


def on_message(client, userdata, msg):
    global client_counter

    with lock:

        message_received = msg.payload.decode()
        client_id = message_received.split(",")[0]

        client_messages[client_id] = message_received
        print(message_received)
        print(client_id)
        client_counter += 1

        if client_id not in client_messages:
            client_counter += 1

        if client_counter >= 3:
            for client_id, message in client_messages.items():
                response = f"Gj {client_id}"
                client.publish(f"{client_id}_response", response)


def on_publish(client, userdata, mid):
    print("Message Published")


def on_disconnect(client, userdata, rc):
    print(f"Disconnected with result code {rc}")


broker_address = "localhost"
broker_port = 1883

server = mqtt.Client()
server.on_connect = on_connect
server.on_message = on_message
server.on_publish = on_publish
server.on_disconnect = on_disconnect

server.connect(broker_address, broker_port, 60)

try:
    server.loop_start()
    server.subscribe("your_topic")

    while client_counter < 3:
        pass

except KeyboardInterrupt:
    print("Server shutting down")

finally:
    server.loop_stop()
    server.disconnect()
