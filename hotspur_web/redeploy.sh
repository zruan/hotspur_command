#!/bin/bash

docker build -t hotspur_web .
docker stop hotspur_web_container
docker rm hotspur_web_container

docker run -d --name hotspur_web_container -v /scratch:/scratch -p 80:80 hotspur_web
