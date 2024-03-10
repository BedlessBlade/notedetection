import cv2
import numpy as np
import socket
import struct

UDP_IP = "127.0.0.1"
UDP_PORT = 5008


#init
fromcenter = 0.0
#Constants
target_hex = "#8A1C1D" #Target color
tolerance = 10 #Color tolerance (lower=more accurate higher=less accurate but picks up the note better) (35 is about the limit before it starts picking up random stuff)
cameraid = 0 #camera ID
minpixel = 40 #minimum pixels for any output other than raw
centertolerance = 0.15 #tolerance for accepted center
#Hex converter
def hex_to_hsv(hex_color):
  hex_color = hex_color.lstrip('#')
  rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
  hsv = cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2HSV)[0][0]
  return hsv

target_hsv = hex_to_hsv(target_hex)

#Open camera stream
cap = cv2.VideoCapture(cameraid)

while True:
    ret, frame = cap.read()

    #noone cares
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    width = frame.shape[1]

    #Create the left and right masks
    left_mask = np.zeros_like(hsv_frame[:,:,0])
    right_mask = np.zeros_like(left_mask)

    lower = np.array([
        max(0, target_hsv[0] - tolerance),
        max(0, target_hsv[1] - tolerance),
        max(0, target_hsv[2] - tolerance)
    ])
    upper = np.array([
        min(180, target_hsv[0] + tolerance), 
        min(255, target_hsv[1] + tolerance),
        min(255, target_hsv[2] + tolerance)
    ])

    #more mask stuff
    left_mask = cv2.inRange(hsv_frame[:, :width//2], lower, upper)
    right_mask = cv2.inRange(hsv_frame[:, width//2:], lower, upper)

    # i dont even know
    left_count = cv2.countNonZero(left_mask)
    right_count = cv2.countNonZero(right_mask)

    if right_count > left_count and right_count > minpixel:
        difference = left_count/right_count
        fromcenter = (1 - difference)
    elif left_count > right_count and left_count > minpixel:
        difference = right_count/left_count
        fromcenter = (1 - difference) * -1
    elif left_count == right_count and left_count > minpixel:
        difference = 0
        fromcenter = 0

    if abs(fromcenter) < centertolerance:
        fromcenter = 0

    print(str(fromcenter) + " " + str(left_count) + " : " + str(right_count))
    # Convert the float into bytes 
    MESSAGE = struct.pack('!f', fromcenter) 

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))



    fromcenter = 0.0
  

cap.release()
cv2.destroyAllWindows()
