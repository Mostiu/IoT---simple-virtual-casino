import paho.mqtt.client as mqtt
import time
from PIL import Image, ImageDraw, ImageFont
import lib.oled.SSD1331 as SSD1331
import RPi.GPIO as GPIO
from config import *  # pylint: disable=unused-wildcard-import
import neopixel
import board
from mfrc522 import MFRC522

global executing
executing = False
pixels = neopixel.NeoPixel(board.D18, 8, brightness=1.0 / 32, auto_write=False)

def buzzer_state(state):
    GPIO.output(buzzerPin, not state)  # pylint: disable=no-member

def play_animation(sound=True):
    global executing
    executing = True
    sleep_time = 0.25
    times = 5
    while executing:
        for i in range(0, 8):
            if i % 2 == 0:
                pixels[i] = (255, 0, 0)
            else:
                pixels[i] = (0, 255, 0)
            pixels.show()
            if sound:
                buzzer_state(True)
            time.sleep(sleep_time)

        for i in range(0, 8):
            if i % 2 == 1:
                pixels[i] = (255, 0, 0)
            else:
                pixels[i] = (0, 255, 0)
            pixels.show()
            if sound:
                buzzer_state(False)
            time.sleep(sleep_time)
        times = times - 1
        if times == 0:
            executing = False
    pixels.fill((0, 0, 0))
    pixels.show()
    buzzer_state(False)

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

    def oled_display_game_result(self, result_message):
        disp = SSD1331.SSD1331()
        disp.Init()
        disp.clear()
        image1 = Image.new("RGB", (disp.width, disp.height), "WHITE")
        draw = ImageDraw.Draw(image1)
        fontLarge = ImageFont.truetype("./lib/oled/Font.ttf", 20)
        fontSmall = ImageFont.truetype("./lib/oled/Font.ttf", 13)
        draw.text((8, 0), result_message, font=fontLarge, fill="WHITE")

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

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")

    def on_history(self, client, userdata, msg):
        print(f"Received history response: {msg.payload.decode()}")

    def on_game(self, client, userdata, msg):
        message_decoded = (str(msg.payload.decode("utf-8"))).split(".")
        print(f"Received game response: {message_decoded[0]}")

    def on_publish(self, client, userdata, mid):
        print(f"Message Published with MID: {mid}")

    def on_disconnect(self, client, userdata, rc):
        print(f"Disconnected with result code {rc}")

    def connect_to_broker(self):
        self.client.connect(self.broker_address, self.broker_port, 60)

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
                print("add card")
                player_id = self.read_rfid_card()
                print(player_id)
                if choice.lower() == 'history':
                    message = f"{self.client_id},{player_id}"
                    self.publish_message(choice, message)
                elif choice.lower() == "game":
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
        if topic == 'game':
            play_animation()

if __name__ == "__main__":
    broker_address = "0.0.0.0"
    broker_port = 1883
    client_id = "client1"
    interactive_client = InteractiveMQTTClient(broker_address, broker_port, client_id)
    interactive_client.connect_to_broker()
    interactive_client.start()
