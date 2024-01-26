#!/usr/bin/env python3mqtt

# pylint: disable=no-member

import time
from tkinter.tix import DirTree
import RPi.GPIO as GPIO
from config import * # pylint: disable=unused-wildcard-import
from mfrc522 import MFRC522
from datetime import datetime
import paho.mqtt.client as mqtt
import tkinter
import neopixel
import board
import random
import json

executing = True

class Game:
    players_card_ids = []
    players_bets = []
    player_wins = [] # 0 - loose, 1 - win
    time = None

    

terminal_id = "T0"
broker = "localhost"
client = mqtt.Client()
pixels = neopixel.NeoPixel(
board.D18, 8, brightness=1.0/32, auto_write=False)

def greenColorBlink():
    pixels.fill((0, 255, 0))
    pixels.show()
    time.sleep(1)
    pixels.fill((0, 0, 0))
    pixels.show()
    # first pixel red
    # pixels[0] = (255, 0, 0)


def redColorBlink():
    pixels.fill((255, 0, 0))
    pixels.show()
    time.sleep(1)
    pixels.fill((0, 0, 0))
    pixels.show()


def buttonPressedCallback(channel):
    global executing
    executing = False

def buzzer_state(state):
    GPIO.output(buzzerPin, not state) # pylint: disable=no-member

def buzzer():
    buzzer_state(True)
    time.sleep(1)
    buzzer_state(False)

def buzzer_green():
    buzzer_state(True)
    pixels.fill((0, 255, 0))
    pixels.show()
    time.sleep(1)
    buzzer_state(False)
    pixels.fill((0, 0, 0))
    pixels.show()

def buzzer_red():
    buzzer_state(True)
    pixels.fill((255, 0, 0))
    pixels.show()
    time.sleep(0.5)
    buzzer_state(False)
    pixels.fill((0, 0, 0))
    pixels.show()

def play_lottery_animation(n):
    for i in range(0, n):
        for i in range(0, 8):
            if i % 2 == 0:
                pixels[i]((255, 0, 0))
            else:
                pixels[i]((0, 255, 0))
        pixels.show()
        buzzer_state(True)
        time.sleep(0.25)
        buzzer_state(False)
        for i in range(0, 8):
            if i % 2 == 0:
                pixels[i]((0, 255, 0))
            else:
                pixels[i]((255, 0, 0))
        pixels.show()
        time.sleep(0.25)

def rfidRead():
    global executing
    MIFAREReader = MFRC522()
    last_scan = datetime.timestamp(datetime.now()) - 0.2
    last_id = 0
    while executing:

        if datetime.timestamp(datetime.now()) - last_scan > 0.2:
            (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
            if status == MIFAREReader.MI_OK:
                (status, uid) = MIFAREReader.MFRC522_Anticoll()
                if status == MIFAREReader.MI_OK:
                    dt = datetime.now()
                    num = 0
                    for i in range(0, len(uid)):
                        num += uid[i] << (i*8)
                    if last_id == uid and datetime.timestamp(dt) - last_scan < 5.0:
                        continue
                    elif num != 981114580761:
                        buzzer_red()
                        buzzer_red()
                    else:
                        buzzer_green()
                    last_scan = datetime.timestamp(datetime.now())
                    last_id = uid
                    print(f"Card read UID: {num}")
                    print(f"Date and time of scanning: {dt}")
                    call_worker(num, dt)
                    # simpleLedTest()
                    last_scan = datetime.timestamp(datetime.now())

def readOneCard():
    ready = False
    MIFAREReader = MFRC522()
    while not ready:
        (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
        if status == MIFAREReader.MI_OK:
            (status, uid) = MIFAREReader.MFRC522_Anticoll()
            if status == MIFAREReader.MI_OK:
                num = 0
                for i in range(0, len(uid)):
                    num += uid[i] << (i*8)
                print(f"Card read UID: {num}")
                ready = True
                return num

def call_worker(worker_id, dt):
    if worker_id == 981114580761:
        # wprowadzenie n graczy do ruletki
        n = input("Podaj liczbe graczy: ")

        #  kazdy gracz wpisuje kwote i R/G/liczba(1,37)
        game = Game()
        game.time = str(dt)
        for i in range(n):
            # scan player card
            game.players_card_ids.append(readOneCard())

            # scan player bet
            bet = input("Podaj zaklad: ")
            if bet == "R":
                game.players_bets.append("R")
            elif bet == "G":
                game.players_bets.append("G")
            else:
                game.players_bets.append(int(bet))
        
        #  losowanie liczby
        play_lottery_animation(5)
        winning_number = random.randint(1, 38)

        #  sprawdzenie wygranych
        for i in range(n):
            if game.players_bets[i] == "R" and winning_number % 2 == 1:
                game.player_wins.append(1)
            elif game.players_bets[i] == "G" and winning_number % 2 == 0:
                game.player_wins.append(1)
            elif game.players_bets[i] == winning_number:
                game.player_wins.append(1)
            else:
                game.player_wins.append(0)
        
        #  wyslanie wygranych do graczy
        
        client.publish("dealer/start", json.dumps(game))
    else:
        client.publish("client/card", str(worker_id) + " - " + str(dt) + " - entry denied")
        buzzer_red()
        print("Message sent to broker")

def connect_to_broker():
    client.connect(broker)
    call_worker("Client connected", datetime.now())
    print("Connected to broker")

def disconnect_from_broker():
    call_worker("Client disconnected", datetime.now())
    client.disconnect()
    print("Disconnected from broker")


def test():
    GPIO.add_event_detect(buttonRed, GPIO.FALLING, callback=buttonPressedCallback, bouncetime=200)

    print('Place the card close to the reader (on the right side of the set).')
    connect_to_broker()
    rfidRead()
    disconnect_from_broker()



if __name__ == "__main__":
    test()
    GPIO.cleanup() # pylint: disable=no-member