#!/bin/bash

sudo apt-get update && sudo apt-get install -y apt-transport-https

sudo apt install docker.io

sudo systemctl start docker

sudo systemctl stop docker
