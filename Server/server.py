import paho.mqtt.client as mqtt
import threading
import random
from GameDatabase import GameDatabase


class GameServer:
    def __init__(self, broker_address, broker_port):
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.server = mqtt.Client()
        self.num_clients = 0
        self.client_messages = {}
        self.messages_sent = 0
        self.is_active_game = False
        self.lock = threading.Lock()
        self.db = GameDatabase()

        # Set up MQTT callbacks
        self.server.on_connect = self.on_connect
        self.server.on_publish = self.on_publish
        self.server.on_disconnect = self.on_disconnect
        self.server.message_callback_add("history", self.on_history)
        self.server.message_callback_add("game", self.on_game)

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe("game")
        client.subscribe("history")

    def on_history(self, client, userdata, msg):
        message = msg.payload.decode()
        data = message.split(",")
        response = self.db.get_history_for_player(data[1])
        client.publish(f"{data[0]}_history_response", response)

    def on_game(self, client, userdata, msg):
        with self.lock:
            message_received = msg.payload.decode()
            data = message_received.split(",")
            player_id = data[3]
            self.client_messages[player_id] = data
            print(self.client_messages)
            if len(self.client_messages.keys()) >= self.num_clients:
                self.play_game()

    def play_game(self):
        rolled_number = random.randint(1, 37)
        rolled_color = "red" if rolled_number % 2 == 0 else "black"
        logs = []
        for key, message in self.client_messages.items():
            win = message[2] == rolled_color or message[2] == str(rolled_number)
            if win:
                response = f"You won {message[3]} - your bet: {message[2]} rolled: {rolled_number} {rolled_color}"
            else:
                response = f"You lost {message[3]} - your bet: {message[2]} rolled: {rolled_number} {rolled_color}"
            self.server.publish(f"{message[0]}_response", response)
            print(f"Sent response to {message[0]}")
            self.messages_sent += 1
            payout = 2 * int(message[1]) if win else -int(message[1])
            logs.append(f"{message[0]},{message[3]},{message[2]},{message[1]},{rolled_number},{win},{payout}")
        self.client_messages.clear()
        self.db.insert_logs(logs)
        logs.clear()

    def on_publish(self, client, userdata, mid):
        return

    def on_disconnect(self, client, userdata, rc):
        print(f"Disconnected with result code {rc}")
        self.db.close_connection()

    def start(self):
        self.server.connect(self.broker_address, self.broker_port, 60)
        self.server.loop_start()

        try:
            while True:
                self.server.subscribe("game")
                self.server.subscribe("history")
                game_name = input("Enter the game name (or 'exit' to quit): ")

                if game_name.lower() == 'exit':
                    break

                try:
                    self.num_clients = int(input("Enter the number of clients: "))
                    self.is_active_game = True
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
                    continue

                while self.is_active_game:
                    print(f"Waiting for {self.num_clients} clients to send messages...")

                    while self.messages_sent < self.num_clients:
                        pass

                    self.messages_sent = 0
                    self.client_messages.clear()

                    next_game = input("Do you want to change the amount of players? (yes/no): ").lower()
                    if next_game == 'yes':
                        self.is_active_game = False


        except KeyboardInterrupt:
            print("Server shutting down")

        finally:
            self.server.loop_stop()
            self.server.disconnect()


if __name__ == "__main__":
    broker_address = "192.168.31.169"
    broker_port = 1883
    game_server = GameServer(broker_address, broker_port)
    game_server.start()

