FROM python:3.8

WORKDIR /app

COPY requirements.txt ./
COPY ./img ./img

RUN apt-get update && apt-get install -y python3-opencv
RUN pip install opencv-contrib-python
RUN pip install -r requirements.txt

COPY ./src/module1.py ./

CMD [ "python", "-u", "./module1.py"]