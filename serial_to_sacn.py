import sys
import serial
import math
import time
from statistics import mean

from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
#import sacn

serial_dev = '/dev/ttyUSB0'
serial_baud = 115200

ser = None

slideHistory = []
rows, cols=16,35
for i in range(rows):
    col = []
    for j in range(cols):
        col.append(0)
    slideHistory.append(col)


state = [True]*16
previousState = [0]*16

#sender = sacn.sACNsender(fps=60)

dmx_vals = [0] * 75

client = udp_client.SimpleUDPClient("192.168.0.104", 10023)
print("Connected!")

def open_serial():
    global ser
    ser = serial.Serial(serial_dev, serial_baud)

def clamp(n, minn, maxn):
        return max(min(maxn, n), minn)

def dampen(slideNumber):
    for i in range(len(slideHistory[slideNumber])-2, -1, -1):
        slideHistory[slideNumber][i+1] = slideHistory[slideNumber][i]

def updateHistory(newValue, slideNumber):
    #for j in range(len(slideHistory)):
    #dampen(slideNumber)

    slideHistory[slideNumber][0] = newValue
    #print(slideHistory)

while True:
    open_serial()
        
    buf = b""
    while True:
        try:
            frag = ser.read(ser.in_waiting)
            buf += frag
            if frag.rfind(b"\n") != -1:
                idx = buf.rfind(b";")
                pieces = buf[:idx].decode("ascii").split(";")
                buf = buf[idx+1:]
                for piece in pieces:
                    if ',' not in piece:
                            continue
                    parts = piece.split(',')
                    ch = int(parts[0])
                    val = int(parts[1])
                    dmx_vals[ch-1] = clamp(val, 0, 255)
                #sender[10].dmx_data = tuple(dmx_vals)

                #print(dmx_vals)
                #print(slideHistory)
                for i in range(1,16):
                    if round(dmx_vals[i+14]/255) == 1 and previousState[i] == 0 :
                        state[i] = not state[i]
                        
                    updateHistory(dmx_vals[i+59]/255,i-1)                                         
                    
                    if state[i]:
                        client.send_message(f"/ch/{i:02}/mix/03/on", 1)
                    else:
                        client.send_message(f"/ch/{i:02}/mix/03/on", 0)

                    previousState[i] = dmx_vals[i+14]/255
            for i in range(len(slideHistory)):
                dampen(i)
                client.send_message(f"/ch/{i:02}/mix/03/level", mean(slideHistory[i-1]))

            time.sleep(0.003)
        except Exception as e:
            print("Error occured, let's try again", str(e))
            #raise e
        
        

"""
if __name__ == "__main__":
    client = udp_client.SimpleUDPClient("192.168.0.104", 10023)
    print("Connected!")

    while True:
        client.send_message("/ch/01/mix/fader", ((math.sin(time.time()*10)+1)/2) )
        time.sleep(0.01)

        for i in range(1,17):
            client.send_message(f"/ch/{i:02}/mix/fader", ((math.sin((time.time()+1/16*i)*10)+1)/2))
"""