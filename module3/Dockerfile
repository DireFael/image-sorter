FROM python:3.8

WORKDIR /app

COPY requirements.txt ./

RUN apt-get update && apt-get install -y python3-opencv
RUN pip install opencv-contrib-python
RUN pip install -r requirements.txt

COPY ./src/module3.py ./
RUN mkdir -p ./sorted

CMD [ "python", "-u", "./module3.py"]