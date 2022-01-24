#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time

import numpy as np
import paho.mqtt.client as mqtt
import webcolors


BROKER_ADRESS = "mosquitto"
BROKER_PORT = 1883
CLIENT_ID = "Modul 2"
TOPIC_TO_PUBLISH_STATUS = "image/status"
TOPIC_TO_PUBLISH_COLOR = "image/color"
TOPIC_TO_SUBSCRIBE = "image/#"



def tranform_bgr_to_rgb(color_array):
    """
    Function transform data in BGR color mode to RGB color mode
    """
    
    return (color_array[2], color_array[1], color_array[0])

def get_nearest_web_color(requested_color):
    """
    Function searching nearest color. USING CSS3 extended color space. Calculate difference between our color and defined color.
    Difference of each color save to dict after calculate all, pick the color with the smallest difference as probable color.
    """

    probably_colors_dict = {}

    for hex_color, name_color in webcolors.CSS3_HEX_TO_NAMES.items():

        probable_red, probable_green, probable_blue = webcolors.hex_to_rgb(hex_color)

        # Calculating difference of each color components 
        diff_red = (probable_red - requested_color[0]) ** 2
        diff_green = (probable_green - requested_color[1]) ** 2
        diff_blue = (probable_blue - requested_color[2]) ** 2

        probably_colors_dict[(diff_red + diff_green + diff_blue)] = name_color

    return probably_colors_dict[min(probably_colors_dict.keys())]

def get_average_color(img_data):
    """
    Function calculate average value for all rows then calculate average value from each average color row
    Return array where each color component have own average value
    """

    avg_color_per_row = np.average(img_data, axis=0)
    average_color = np.average(avg_color_per_row, axis=0)

    return tranform_bgr_to_rgb(average_color)

def parse_and_validate_message_content(message):
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
        return None

    if "imagename" not in json_data or "imagedata" not in json_data or "checksum" not in json_data:

        print(f"{CLIENT_ID}:In recieved data not found 'imagename' or 'imagedata' or 'checksum'")
        return None
        
    return json_data

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

def publish_to_broker(client, message, topic):
    """
    Function publish message into topic
    """

    result = client.publish(topic, str(message))
    status = result[0]

    if status != 0:

        print(f"{CLIENT_ID}:Failed to send message to topic '{topic}'")

def subscribe_to_topic(client, topic):
    """
    Function for subscribe to specific topic 
    """

    def on_message(client, userdata, message):

        # Receiving data from module 1  
        if message.topic == "image/data":

            json_data = parse_and_validate_message_content(message)

            if not json_data:
                return

            image_name = json_data['imagename']
            # Transforming back list of lists to np.array. Due to calculate size of image 
            image_data = np.asarray(json_data['imagedata'], dtype=np.uint8)
            image_checksum = json_data['checksum']

            message = {
                'imagename': image_name
            }

            # Checking if image checksum is same as size of image, if not sending message to resend image data
            if image_data.size != image_checksum:

                print(f"{CLIENT_ID}:Image checksum is not same as image size")

                message["imagestatus"] = "invalid"
                topic = TOPIC_TO_PUBLISH_STATUS
            # When checksum is correct, getting nearest color classification and send message to broker with name of color
            else:

                average_color_in_rgb = get_average_color(image_data)
                color_classification = get_nearest_web_color(average_color_in_rgb)
                message["imagecolor"] = color_classification
                topic = TOPIC_TO_PUBLISH_COLOR

            publish_to_broker(client, message, topic)
        
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

            # If image status is END(means all images are processed). Modul will be disconnected from MQTT broker
            if image_status.lower() == "end":
                
                print(f"{CLIENT_ID}:This image was last. Disconnecting this module from broker")

                client.disconnect()
                return
            
    client.subscribe(topic)
    client.on_message = on_message

def main():

    # Wait until MQTT module is fully load and ready to receive messages
    time.sleep(2)
    client = connect_to_broker()
    subscribe_to_topic(client, TOPIC_TO_SUBSCRIBE)

    client.loop_forever()

if __name__ == '__main__':
    main()
