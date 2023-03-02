import sys
import serial
import math
import time
import json
from statistics import mean

from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
#import sacn

serial_dev = '/dev/ttyUSB0'
serial_baud = 115200
configuration = {}

ser = None

slideHistory = []
rows, cols=16,35
for slide in range(rows):
    col = []
    for j in range(cols):
        col.append(0)
    slideHistory.append(col)


state = [True]*16
previousState = [0]*16

#sender = sacn.sACNsender(fps=60)

dmx_vals = [0] * 75

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

with open("settings.json", "r") as settings:
    configuration = json.load(settings)

print(configuration)


client = udp_client.SimpleUDPClient(configuration["config"]["midas_ip"], configuration["config"]["midas_port"])
print(f"Connected to a midas at {configuration['config']['midas_ip']}:{configuration['config']['midas_port']}")

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
                for slide in configuration["slide_config"]:
                    # print(slide)
                    if round(dmx_vals[slide["physicalSlide"]+15]/255) == 1 and previousState[slide["physicalSlide"]] == 0 :
                        state[slide["physicalSlide"]] = not state[slide["physicalSlide"]]
                        
                    updateHistory(dmx_vals[slide["physicalSlide"]+60]/255,slide["physicalSlide"])                                         
                    

                    # Changes here not yet tested!
                    # print(i)

                    for j in slide["levels"]:
                        if state[slide["physicalSlide"]]:
                            client.send_message(f"{j}on", 1)
                        else:
                            client.send_message(f"{j}on", 0)

                    previousState[slide["physicalSlide"]] = dmx_vals[slide["physicalSlide"]+54]/255
            for i in range(len(slideHistory)-1):
                dampen(i)
                #print(configuration['slide_config'][i])
                for j in configuration['slide_config'][i]['levels']:
                    #print(j)
                    #print(f"{j}level")
                    #print(slideHistory[i-1])
                    client.send_message(f"{j}level", mean(slideHistory[i-1]))

            time.sleep(0.003)
        except Exception as e:
            print("Error occured, let's try again", str(e))
            raise e
        
        

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