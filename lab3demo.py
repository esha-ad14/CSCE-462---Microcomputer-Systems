import time
import matplotlib.pyplot as plt 
#import numpy as np 
import os
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn 


spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D22)
mcp = MCP.MCP3008(spi, cs)
chan0 = AnalogIn(mcp, MCP.P0)

def dataGathering():
    voltArr = []
    timeArr = []
    startT = time.time()
    while time.time() - startT < 1: #gather 1s of data points
        voltArr.append(chan0.voltage)
        timeArr.append(time.time()-startT)
        
    smoothVolt = []
    smoothVolt.append(voltArr[0])
    for i in range(1, len(voltArr)-1): #smooth data with rolling average spanning 3 numbers
        avg = (voltArr[i-1] + voltArr[i] + voltArr[i+1]) / 3
        smoothVolt.append(avg)
    smoothVolt.append(voltArr[len(voltArr)-1])
    
    #plot the 1s of data to prove the actual frequency output by the function generator (we used our generator from lab 2 on another Pi)
    #plt.plot(timeArr, voltArr)
    #  plt.show()

    return voltArr, smoothVolt, timeArr


#Waveform Characterization
def characterizeWaveform(rawVoltageList, voltArr, timeArr):
    size = len(voltArr)
    max = 0.0
    min = 100000000.0
    for i in range(size): #obain max and min from smoothed voltage list
        if (voltArr[i] > max):
            max = voltArr[i]
        if (voltArr[i] < min):
            min = voltArr[i]
        if (i == size - 1):
            continue
        
    #test if it is a square wave
    numMin = 0
    numMax = 0
    tolerance = (max-min) * 0.1 #tolerance  for noise 
    for i in range(size): #determine amount of points on extremes
        if max - voltArr[i] < tolerance:
            numMax = numMax + 1
        elif voltArr[i] - min < tolerance:
            numMin = numMin + 1
    if numMin + numMax > (size * 0.8): #if at 80% of points lie on extremes it is a square wave
        print("Square")
        squareFreq(rawVoltageList, timeArr, min, max)
        return

    #test if its a triangle or sin wave   
    edgeArr = []
    start = -1
    end = -1
    side = -1 #0 is falling side, 1 is rising
    fluctuation = 0 #account for fluctuations
    for i in range(1, size): #find one continuous edgeArr (rising or falling) and store the start and end indices
        if (voltArr[i] - voltArr[i-1] >= 0):
            if (side == -1):
                side = 1
            elif (side == 0):
                fluctuation = fluctuation + 1
                if (fluctuation >= 5): #account for noise causing fluctuations
                    if (start == -1):
                        start = i-1 - fluctuation
                        side = 1
                    else:
                        end = i-1 - fluctuation
                        break           
            else:
                fluctuation = 0
        else:
            if (side == -1):
                side = 0
            elif (side == 1):
                fluctuation = fluctuation + 1
                if (fluctuation >= 5): #account for noise causing fluctuations
                    if (start == -1):
                        start = i-1 - fluctuation
                        side = 0
                    else:
                        end = i-1 - fluctuation
                        break
            else:
                fluctuation = 0
    for i in range(start+1, end): #use the indices to store the change in voltage between each point
        edgeArr.append(voltArr[i-1]-voltArr[i])
    sum = 0
    #obtain average change between points
    for i in range(len(edgeArr)):
        sum = sum + edgeArr[i]
    #print(len(edgeArr))
#     IncrAvg = sum / len(edgeArr)
    IncrAvg = sum / 3
    #count the number of changes in two consecutive points that equal the average for the edgeArr
    nIncrAvg = 0
    tolerance = (max-min) * 0.0075 #tolerance to account for noise (experimentally determined)
    for i in range(len(edgeArr)):
        if abs(IncrAvg - edgeArr[i]) < tolerance:
            nIncrAvg = nIncrAvg + 1
    if nIncrAvg >     len(edgeArr) * 0.5: #if 50% (experimentally determined) of the increases were equal to the average it is a triangle
        print("Triangle")
        sinTriangleFreq(voltArr, timeArr, min, max)
    else:
        print("Sin")
        sinTriangleFreq(voltArr, timeArr, min, max)



#Frequencies 
def squareFreq(voltArr, timeArr, min, max):
    size = len(voltArr)
    tolerance = (max-min) * 0.2
    maxStart = -1
    maxFinish = -1
    minStart = -1
    minFinish = -1
    lastExtreme = -1 #-1 for no last extreme, 0 for min, 1 for max
    for i in range (size): #find a series of consecutive maxes and mins - the longer of which is half a cycle
        if max - voltArr[i] < tolerance:
            if lastExtreme == 0:
                minFinish = i-1
                if maxStart != -1:
                    break
            lastExtreme = 1
            if maxStart == -1:
                maxStart = i
        elif voltArr[i] - min < tolerance:
            if lastExtreme == 1:
                maxFinish = i-1
                if minStart != -1:
                    break
            lastExtreme = 0
            if minStart == -1:
                minStart = i
        
    maxTime = timeArr[maxFinish] - timeArr[maxStart]
    minTime = timeArr[minFinish] - timeArr[minStart]
    if maxTime > minTime:
        freq = 1.0 / 2.0 / maxTime
    elif(maxTime == minTime):
        print('')
    else:
       # print(minTime)
        freq = 1.0 / 2.0 / minTime
    print(str(freq) + "Hz")

def sinTriangleFreq (voltArr, timeArr, min, max):
    size = len(voltArr)
    tolerance= (max-min) * 0.05
    min1 = -1
    min2 = -1
    maxSeen = False
    for i in range (size): #find 2 minimum points, a maximum must be inbetween - indicates one full cycle
        if voltArr[i] - min < tolerance:
            minSeen = True
            if min1 == -1:
                min1 = i
            elif maxSeen:
                min2 = i
                break
        elif max - voltArr[i] < tolerance:
            if min1 == -1:
                continue
            maxSeen = True
    freq = 1 / (timeArr[min2] - timeArr[min1])
    print(str(freq) + "Hz")
    
while True:
    rawVoltageList, smoothVolt, timeArr = dataGathering()
    characterizeWaveform(rawVoltageList, smoothVolt, timeArr)
  