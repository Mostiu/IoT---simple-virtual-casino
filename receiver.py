#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import time
import os

broker = "localhost"

client = mqtt.Client()

def process_message(client, userdata, message):
    curr_dir = os.getcwd()
    file_path = os.path.join(curr_dir, 'output.txt')
    message_decoded = str(message.payload.decode("utf-8"))
    with open(file_path, 'a') as file:
        file.write(message_decoded + '\n')
        print(message_decoded)

def connect_to_broker():
    client.connect(broker)

    client.on_message = process_message

    client.subscribe("worker/card")
    while client.loop() == 0:
        pass


def disconnect_from_broker():
    client.loop_stop()
    client.disconnect()


def run_receiver():
    connect_to_broker()
    disconnect_from_broker()


if _name_ == "_main_":
    run_receiver()