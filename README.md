# web-cam-security
A Flask/Python app that lets you stream a Webcam and saves automatically a photo every time it detects movement. 

After cloning the repo you can run the app with 
```
pyhton3 app.py
```
and after that you can go to:

```
127.0.0.1:5000/
```
to check the photos stored of movement detection and 
```
127.0.0.1:5000/video
```
to check the live stream. Works best with Chrome/Chromium.


You will need to install with pip3:
* flask
* json
* threading 
* OpenCV2/3

You can reset the database with the script removecontent.sh
