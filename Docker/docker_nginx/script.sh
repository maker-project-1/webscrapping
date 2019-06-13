#!/bin/bash
sudo docker run -d -p 8080:80 -v $(pwd):/usr/share/nginx/html --name="site" nginx