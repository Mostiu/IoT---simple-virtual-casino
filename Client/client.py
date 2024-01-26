import paho.mqtt.client as mqtt
import time


def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")


def on_history(client, userdata, msg):
    print(f"Received history response: {msg.payload.decode()}")


def on_game(client, userdata, msg):
    print(f"Received game response: {msg.payload.decode()}")


def on_publish(client, userdata, mid):
    print(f"Message Published with MID: {mid}")


def on_disconnect(client, userdata, rc):
    print(f"Disconnected with result code {rc}")


broker_address = "localhost"
broker_port = 1883
client_id = "client1"

client = mqtt.Client()
client.on_connect = on_connect
client.on_publish = on_publish
client.on_disconnect = on_disconnect

# Pass client_id as userdata to on_history and on_game callbacks
client.message_callback_add(f"{client_id}_history_response", on_history)
client.message_callback_add(f"{client_id}_response", on_game)
client.user_data_set({"client_id": client_id})

client.connect(broker_address, broker_port, 60)

try:
    client.loop_start()
    client.subscribe(f"{client_id}_response")
    client.subscribe(f"{client_id}_history_response")

    while True:
        choice = input("Enter 'history' or 'game' to choose the type of message (or 'exit' to quit): ")

        if choice.lower() == 'exit':
            break

        if choice.lower() not in ['history', 'game']:
            print("Invalid choice. Please enter 'history', 'game', or 'exit'.")
            continue

        player_id = input("Enter player ID: ")

        if choice.lower() == 'history':
            message = f"{client_id},{player_id}"
            client.publish(choice, message)
        elif choice.lower() == 'game':
            bet_size = input("Enter bet size: ")
            color = input("Enter color (e.g., red, black): ")
            message = f"{client_id},{bet_size},{color},{player_id}"
            client.publish(choice, message)

        time.sleep(1)

except KeyboardInterrupt:
    print("Client shutting down")

finally:
    client.loop_stop()
    client.disconnect()
