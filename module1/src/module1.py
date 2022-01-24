#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import time

import cv2
import paho.mqtt.client as mqtt


BROKER_ADRESS = "mosquitto"
BROKER_PORT = 1883
CLIENT_ID = "Modul 1"
DIR_PATH_IMG = "/app/img"
SUPPORTED_IMAGE_EXTENSION = ("bmp", "jpeg", "jpg", "jpe", "jp2", "png", "webp", "tiff", "tif")
TOPIC_TO_PUBLISH = "image/data"
TOPIC_TO_PUBLISH_END = "image/status"
TOPIC_TO_SUBSCRIBE = "image/status"


def load_images():
    """
    Function for loading image name to list for later use in code
    """

    array_image_names = []
    
    for dir_item in os.listdir(DIR_PATH_IMG):

        if os.path.isdir(f"{DIR_PATH_IMG}/{dir_item}"):
            
            print(f"{CLIENT_ID}:Skipping {dir_item} due to is dir!")
            continue

        # Control if file have supported extension to load as image
        if not dir_item.lower().endswith(SUPPORTED_IMAGE_EXTENSION):
            
            print(f"{CLIENT_ID}:Skipping {dir_item} due to is not supported image extension!")
            continue

        array_image_names.append(dir_item)
    
    return array_image_names

def parse_and_validate_message_content(message, image_list):
    """
    Function parse message received from MQTT broker after that validate format and content in message
    """

    # In MQTT string json have single quote instead of double. Need replace single one to double
    message_content = message.payload.decode().replace("'", "\"")
    
    # Trying load string from MQTT broker to JSON format
    try:

        json_data = json.loads(message_content)

    except ValueError as e:

        print(f"{CLIENT_ID}:Recieved data from '{message.topic}' topic is not json. Recieved data: {message_content}. Error: {e}")
        return None, None
    
    if "imagename" not in json_data or "imagestatus" not in json_data:

        print(f"{CLIENT_ID}:In recieved data not found 'imagename' or 'imagestatus'")

        return None, None

    image_name = json_data['imagename']
    image_status = json_data['imagestatus']

    # Validate if image name in loaded image list
    if image_name not in image_list:

        print(f"{CLIENT_ID}:Invalid image name. Name is not in loaded image list")

        return None, None

    return image_name, image_status.lower()

def connect_to_broker():
    """
    Function connect to MQTT broker and return client
    """

    def on_connect(client, userdata, flags, rc):

        if rc == 0:

            print(f"{CLIENT_ID}:Successfully connected to broker")

        else:

            print(f"{CLIENT_ID}:Failed to connect. Returned {rc}")

    client = mqtt.Client(CLIENT_ID)
    client.on_connect = on_connect
    client.connect(BROKER_ADRESS, BROKER_PORT)

    return client

def prepare_image_data(image_name):
    """
    Function loads image using cv2 lib into np.arrays represent each color as tree item in list and each pixel represent as list of color
    """

    try:

        im = cv2.imread(f"{DIR_PATH_IMG}/{image_name}")

    except cv2.error as e:

        print(f"{CLIENT_ID}:Cannot read file '{image_name}'")
        return {}

    # Making message for send through MQTT broker. np.arrays must be transform to list of lists
    message = {
        "imagename": image_name,
        "imagedata": im.tolist(),
        "checksum": im.size
    }

    return message

def publish_to_broker(client, message, topic):
    """
    Function publish message into topic
    """

    result = client.publish(topic, str(message))
    status = result[0]

    if status != 0:

        print(f"{CLIENT_ID}:Failed to send message to topic '{topic}'")

def subscribe_to_topic(client, topic, image_list):
    """
    Function for subscribe to specific topic 
    """

    def on_message(client, userdata, message):

        image_name, image_status = parse_and_validate_message_content(message, image_list)

        if not image_name or not image_status:
            return

        # If we received status OK, prepare and send another image to classification. If we on end of array, send message with status END
        if image_status == "ok":

            index = image_list.index(image_name)

            if len(image_list) <= (index+1):

                print(f"{CLIENT_ID}:Next index will be out of array index. All image are processed")

                message = {
                    "imagename": image_name,
                    "imagestatus": "end",
                }

                publish_to_broker(client, message, TOPIC_TO_PUBLISH_END)
                client.disconnect()
                return

            print(f"{CLIENT_ID}:Publish to broker next image")

            message = prepare_image_data(image_list[index+1])
            publish_to_broker(client, message, TOPIC_TO_PUBLISH)
        # If we received status INVALID, send same image as last time
        elif image_status == "invalid":

            print(f"{CLIENT_ID}:Publish to broker same image")

            message = prepare_image_data(image_name)
            publish_to_broker(client, message, TOPIC_TO_PUBLISH)

      
    client.subscribe(topic)
    client.on_message = on_message

def main():

    # Wait until MQTT module is fully load and ready to receive messages
    time.sleep(3)
    array_image_names = load_images()

    client = connect_to_broker()
    # Wait before send first image for classification
    time.sleep(0.5)
    message = prepare_image_data(array_image_names[0])
    publish_to_broker(client, message, TOPIC_TO_PUBLISH)
    subscribe_to_topic(client, TOPIC_TO_SUBSCRIBE, array_image_names)

    client.loop_forever()

if __name__ == '__main__':
    main()
