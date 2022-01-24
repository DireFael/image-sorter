#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import time

import cv2
import numpy as np
import paho.mqtt.client as mqtt


BROKER_ADRESS = "mosquitto"
BROKER_PORT = 1883
CLIENT_ID = "Modul 3"
DIR_PATH_FINAL = "/app/sorted"
TOPIC_TO_PUBLISH = "image/status"
TOPIC_TO_SUBSRIBE = "image/#"

image_name = ""
image_data = ""
image_checksum = ""


def save_img_to_dir(name_img, name_dir, img_data):
    """
    Function saves np.array of image using cv2 library into normal image 
    """

    dir_path = f"{DIR_PATH_FINAL}/{name_dir}"

    # Check if color directory exist, if not make them
    if not os.path.exists(dir_path):

        print(f"{CLIENT_ID}:Creating a directory with name '{name_dir}'")
        os.mkdir(dir_path)

    cv2.imwrite(f"{dir_path}/{name_img}", img_data)

def connect_to_broker():
    """
    Function connect to MQTT broker and return client
    """

    def on_connect(client, userdata, flags, rc):

        if rc == 0:

            print(f"{CLIENT_ID}:Successfully connected to broker")

        else:

            print(f"{CLIENT_ID}Failed to connect. Returned {rc}")

    client = mqtt.Client(CLIENT_ID)
    client.on_connect = on_connect
    client.connect(BROKER_ADRESS, BROKER_PORT)

    return client

def publish_to_broker(client, message):
    """
    Function publish message into topic
    """

    result = client.publish(TOPIC_TO_PUBLISH, str(message))
    status = result[0]

    if status != 0:

        print(f"{CLIENT_ID}:Failed to send message to topic '{TOPIC_TO_PUBLISH}'")

def subcribe_to_topic(client, topic):
    """
    Function for subscribe to specific topic 
    """

    def on_message(client, userdata, message):
        
        # Receiving data from module 1
        if message.topic == "image/data":

            # In MQTT string json have single quote instead of double. Need replace single one to double
            message_content = message.payload.decode().replace("'", "\"")

            # Trying load string from MQTT broker to JSON format
            try:

                json_data = json.loads(message_content)

            except ValueError as e:

                print(f"{CLIENT_ID}:Recieved data from '{message.topic}' topic is not json. Recieved data: {message_content}. Error: {e}")
                return
            
            if "imagename" not in json_data or "imagedata" not in json_data or "checksum" not in json_data:

                print(f"{CLIENT_ID}:In recieved data not found 'imagename' or 'imagedata' or 'checksum'")
                return

            # Save image date as global for later use
            global image_name, image_data, image_checksum
        
            # No need check, if the data is incorrect, Module 2 send imagestatus: INVALID
            image_name = json_data['imagename']
            image_data = np.asarray(json_data['imagedata'], dtype=np.uint8)
            image_checksum = json_data['checksum']

        # Receiving data from module 2 about color classification
        elif message.topic == "image/color":

            # In MQTT string json have single quote instead of double. Need replace single one to double
            message_content = message.payload.decode().replace("'", "\"")

            # Trying load string from MQTT broker to JSON format
            try:

                json_data = json.loads(message_content)

            except ValueError as e:

                print(f"{CLIENT_ID}:Recieved data from '{message.topic}' topic is not json. Recieved data: {message_content}. Error: {e}")
                return

            if "imagename" not in json_data or "imagecolor" not in json_data:
                
                print(f"{CLIENT_ID}:In recieved data not found 'imagename' or 'imagecolor'")
                return

            color_image_name = json_data['imagename']
            image_color = json_data['imagecolor']

            # Check if image_name save previously matches with image name contained in message about color, if not send status about invalid image
            if image_name != color_image_name:
                
                message = {
                    "imagename": color_image_name,
                    "imagestatus": "invalid"
                }

            # When names matches, we save data to the appropriate folder 
            else:

                save_img_to_dir(color_image_name, image_color, image_data)
                message = {
                    "imagename": image_name,
                    "imagestatus": "ok"
                }

                print(f"{CLIENT_ID}:Image was successfully saved to folder")

            publish_to_broker(client, message)

        elif message.topic == "image/status":

            message_content = message.payload.decode().replace("'", "\"")

            try:
                json_data = json.loads(message_content)
            except ValueError as e:
                print(f"{CLIENT_ID}:Recieved data from '{message.topic}' topic is not json. Recieved data: {message_content}. Error: {e}")
                return
            
            if "imagename" not in json_data or "imagestatus" not in json_data:
                print(f"{CLIENT_ID}:In recieved data not found 'imagename' or 'imagestatus'")
                return

            image_name = json_data['imagename']
            image_status = json_data['imagestatus']

            # If image status is END(means all images are processed). Modul will be disconnected from MQTT broker. This not due to we want manually control saved data
            if image_status.lower() == "end":
                
                print(f"{CLIENT_ID}:This image was last. Disconnecting this module from broker")

                #client.disconnect()
                return

    client.subscribe(topic)
    client.on_message = on_message

def main():

    # Wait until MQTT module is fully load and ready to receive messages
    time.sleep(2)
    client = connect_to_broker()
    subcribe_to_topic(client, TOPIC_TO_SUBSRIBE)

    client.loop_forever()
    
if __name__ == '__main__':
    main()
