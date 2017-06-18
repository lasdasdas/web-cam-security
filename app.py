#!/usr/bin/python3
import cv2
from flask import Flask, render_template, Response
import threading
import time
import json

#Data contains is an array of dictionaries that contains all the pictures of movement
#location and their timestamp
data = []
try:#In case the file is empty
    with open('detections.txt') as json_data:
        data  = json.load(json_data)
except:
    print("The data file is empty")
print(data)

'''
videothread saves a stream of the webcam and offers the images to the rest of the program
'''

class videothread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.shutdown = False

        self.video = cv2.VideoCapture(0)
        success, image = self.video.read()
        ret , jpeg = cv2.imencode('.jpg', image)
        self.img = jpeg.tobytes()

    def run(self):
        self.update_frame()
    def __del__(self):
        self.video.release()

    def update_frame(self):
        while not self.shutdown:
            success, image = self.video.read()
            if (success):
                ret, jpeg = cv2.imencode('.jpg', image)
                self.img = jpeg.tobytes()

'''
surveillancethread takes the image from videothread and processes it in order to determine
weather there might be movement or not in the frame.
If movement is detected a picture the thread will save a picture
'''
class surveillancethread(threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.shutdown = False
        self.photoevery = 3
        self.timer = time.time()
        self.timer_flag = True
        self.movement_flag = False

    def timercontrol(self):
        if not self.timer_flag:
            if ( time.time()-self.timer )>self.photoevery:
                self.timer = time.time()
                self.timer_flag = True

    def run(self):
        #Get the first frame to compare later
        ret, frame = cvthread.video.read()
        gray1 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)
        glob_contours = []#This vector stores the nº of contours detected each time

        while not self.shutdown:#Thread shutdown
            #Getting the second frame to compare
            ret, frame = cvthread.video.read()
            gray2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)

            #Calculating the delta and the contours
            frameDelta = cv2.absdiff(gray1, gray2)
            thresh = cv2.threshold(frameDelta,15, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            im2, contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

            #glob contour contains the nº of contours of the last 4 measurements
            while len(glob_contours) > 4:
                glob_contours.pop(0)
            glob_contours.append(contours)

            #A mean of the values to naively avoid noise
            mean = 0
            for contiterator in glob_contours:
                mean = len(contiterator) + mean
            #If the mean is avove a certain threshold the movement_flag is actiavted
            if (mean >5):
                self.movement_flag = True
            else:
                self.movement_flag = False

            gray1 = gray2#This frame is now the last frame for the next loop

            #If the timer is not set(no photos saved in the last 3 seconds) and movement_flag is activated
            if (self.movement_flag and self.timer_flag):
                print("Taking picture")
                self.timer_flag = False
                self.timer = time.time()
                #Saving image in static/frame/detection
                cv2.imwrite("static/frame/detection-" + str(round(time.time())) + ".jpg", frame)
                #Writing the entry in the json file
                new_entry = {'Date': time.asctime() , 'Epoch' : time.time() , 'Folder' : "frame/detection-" + str(round(time.time())) + ".jpg" }
                data.append(new_entry)
            self.timercontrol()


'''Flask server:
route / --contains all the photos of movement detections along with their timestamp
route /video --contains a stream of the cam as implemented in https://blog.miguelgrinberg.com/post/video-streaming-with-flask

'''
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('base.html'  , pages=data)

def gen():
    while True:
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + cvthread.img+ b'\r\n\r\n')

@app.route('/video')
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    #Launch opencv stream thread
    cvthread = videothread(3, str(time.time))
    cvthread.start()
    #Launch the surveillancethread, needs opencv thread to be launched
    surthread = surveillancethread(1, str(time.time))
    surthread.start()
    #Launch Flask server
    app.run(threaded=True ,  host='0.0.0.0' )
    #Once exited Flask with control + C save the new data entries to detections.txt
    with open("detections.txt", "w") as outfile:
        json.dump(data, outfile)
    print("Exiting server")
    #Finish the threads
    cvthread.shutdown = True
    surthread.shutdown = True
    cvthread.join()
    surthread.join()
