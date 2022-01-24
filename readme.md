
# Color-based image sorter
Simple color-based image sorter. It consists of 3 modules. The first module loads images from a folder. Second module then calculates the average color in the image within RGB values. It converts them to color names according to the [web color - CSS3 extended colors](https://en.wikipedia.org/wiki/Web_colors). Third module saves the image to the folder according to its color classification. The modules communicate with each other using the MQTT protocol. [Mosquitto](https://mosquitto.org) is used here as a broker.


# How to use
In first to download project

```
git clone {{link}} 
```

In folder ``image-sorter`` run:
```
docker-compose up
```

The scripts are now running and classifying the test images in the ``image-sorter/img`` folder. After the scripts run out of images, they disconnect from the MQTT broker. Except for the last script, into which you can connect and check the classification of individual images.

# Unit test
They are not implemented within docker-composer. However, in the ``tests`` folder there is a sample of unitt tests for all 3 modules.

# Extensions
There is a large possibility to extend its functionality. However, these would mean more robust code and for now I tried to keep it simple as possible. 