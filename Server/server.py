import paho.mqtt.client as mqtt
import threading
import random

client_messages = {}
client_counter = 0
messages_sent = 0
is_active_game = False
lock = threading.Lock()


def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("game")
    client.subscribe("history")


def on_history(client, userdata, msg):
    message = msg.payload.decode()
    data = message.split(",")
    response = f"Your history, {data[1]}"
    client.publish(f"{data[0]}_history_response", response)


def on_game(client, userdata, msg):
    global client_counter
    global is_active_game
    global messages_sent
    with lock:
        message_received = msg.payload.decode()
        data = message_received.split(",")
        player_id = data[3]
        client_messages[player_id] = data
        print(client_messages)
        if len(client_messages.keys()) >= num_clients:
            rolled_number = random.randint(1, 37)
            rolled_color = "red" if rolled_number % 2 == 0 else "black"
            for key, message in client_messages.items():
                if message[2] == rolled_color or message[2] == str(rolled_number):
                    response = f"You won {message[3]} - your bet: {message[2]} rolled: {rolled_number} {rolled_color}"
                else:
                    response = f"You lost {message[3]} - your bet: {message[2]} rolled: {rolled_number} {rolled_color}"
                client.publish(f"{message[0]}_response", response)
                print(f"Sent response to {message[0]}")
                messages_sent += 1
            client_messages.clear()


def on_publish(client, userdata, mid):
    global client_counter
    global messages_sent
    client_counter = 0


def on_disconnect(client, userdata, rc):
    print(f"Disconnected with result code {rc}")


broker_address = "156.17.237.62"
broker_port = 1883

server = mqtt.Client()
server.on_connect = on_connect
server.on_publish = on_publish
server.on_disconnect = on_disconnect
server.message_callback_add("history", on_history)
server.message_callback_add("game", on_game)

server.connect(broker_address, broker_port, 60)

try:
    server.loop_start()
    while True:
        server.subscribe("game")
        server.subscribe("history")
        game_name = input("Enter the game name (or 'exit' to quit): ")

        if game_name.lower() == 'exit':
            break

        try:
            num_clients = int(input("Enter the number of clients: "))
            is_active_game = True
        except ValueError:
            print("Invalid input. Please enter a valid number.")
            continue

        while is_active_game:
            print(f"Waiting for {num_clients} clients to send messages...")

            while messages_sent < num_clients:
                pass
            client_counter = 0
            messages_sent = 0
            client_messages.clear()

            next_game = input("Do you want to change the amount of players? (yes/no): ").lower()
            if next_game == 'yes':
                is_active_game = False
                break

except KeyboardInterrupt:
    print("Server shutting down")

finally:
    server.loop_stop()
    server.disconnect()
