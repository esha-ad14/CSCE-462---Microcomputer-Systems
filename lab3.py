import time
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
    startT = time.time()
    voltArr = []
    timeArr = []
    while time.time() - startT < 1:
        voltArr.append(chan0.voltage)
        timeArr.append(time.time()-startT)    
    smoothVolt = []
    smoothVolt.append(voltArr[0])
    for i in range(1, len(voltArr)-1): 
        avg = (voltArr[i-1] + voltArr[i] + voltArr[i+1]) / 3
        smoothVolt.append(avg)
    smoothVolt.append(voltArr[len(voltArr)-1])
    return voltArr, smoothVolt, timeArr


#Waveform Characterization
def characterizeWaveform(rawVoltageList, voltArr, timeArr):
    size = len(voltArr)
    max = 0.0
    min = 100000000.0
    for i in range(size): 
        if (voltArr[i] > max):
            max = voltArr[i]
        if (voltArr[i] < min):
            min = voltArr[i]
        if (i == size - 1):
            continue     
    #square wave
    minN = 0
    maxN = 0
    tolerance = (max-min) * 0.1 
    for i in range(size): 
        if max - voltArr[i] < tolerance:
            maxN += 1
        elif voltArr[i] - min < tolerance:
            minN += 1
    if minN + maxN > (size * 0.8): 
        print("Square")
        square(rawVoltageList, timeArr, min, max)
        return

    # triangle or sin wave   
    edgeArr = []
    start = -1
    end = -1
    side = -1 
    fluctuation = 0 
    for i in range(1, size): 
        if (voltArr[i] - voltArr[i-1] >= 0):
            if (side == -1):
                side = 1
            elif (side == 0):
                fluctuation += 1
                if (fluctuation >= 5): 
                    if (start == -1):
                        start = [i-1] - fluctuation
                        side = 1
                    else:
                        end = [i-1] - fluctuation
                        break           
            else:
                fluctuation = 0
        else:
            if (side == -1):
                side = 0
            elif (side == 1):
                fluctuation += 1
                if (fluctuation >= 5): 
                    if (start == -1):
                        start = [i-1] - fluctuation
                        side = 0
                    else:
                        end = [i-1] - fluctuation
                        break
            else:
                fluctuation = 0
    
    for i in range(0, end):
        edgeArr.append(voltArr[i-1]-voltArr[i])
      
    sum = 0
    for i in range(len(edgeArr)):
        sum = sum + edgeArr[i]
    
    IncrAvg = sum / 3
    
    nIncrAvg = 0
    tolerance = (max-min) * 0.075 
    for i in range(len(edgeArr)):
        if abs(IncrAvg - edgeArr[i]) < tolerance:
            nIncrAvg +=1
    if (nIncrAvg < len(edgeArr) * 0.5): 
    if ((nIncrAvg!=0) and (len(edgeArr)!=0)):
        if((len(edgeArr) / (nIncrAvg)) < 3):
           print("Triangle")
            sinTri(voltArr, timeArr, min, max)
        else:
            print("Sin")
           sinTri(voltArr, timeArr, min, max)
    else:

    print('--------------')

#Frequencies 
def square(voltArr, timeArr, min, max):
    size = len(voltArr)
    tolerance = (max-min) * 0.2
    maxS, maxf, minS, minf, last  = -1
    for i in range (size): 
        if max - voltArr[i] < tolerance:
            if last == 0:
                minf = [i-1]
                if maxS != -1:
                    break
            last = 1
            if maxS == -1:
                maxS = i
        elif voltArr[i] - min < tolerance:
            if last == 1:
                maxf = i-1
                if minS != -1:
                    break
            last = 0
            if minS == -1:
                minS = i
        
    maxTime = timeArr[maxf] - timeArr[maxS]
    minTime = timeArr[minf] - timeArr[minS]

    if maxTime > minTime:
        freq = 1.0 / 2.0 / maxTime
    elif(maxTime == minTime):
        print('')
    else:
        print(minTime)
        freq = 1.0 / 2.0 / minTime
    print(str(freq) + "Hz")

def sinTri (voltArr, timeArr, min, max):
    size = len(voltArr)
    tolerance= (max-min) * 0.05
    min1 = -1
    min2 = -1
    lastVis = False
    for i in range (size): 
        if voltArr[i] - min < tolerance:
            minSeen = True
            if min1 == -1:
                min1 = i
            elif lastVis:
                min2 = i
                break
        elif max - voltArr[i] < tolerance:
            if min1 == -1:
                continue
            lastVis = True
    freq = 1 / (timeArr[min2] - timeArr[min1])
    print(str(freq) + "Hz")
    
while True:
    rawVoltageList, smoothVolt, timeArr = dataGathering()
    characterizeWaveform(rawVoltageList, smoothVolt, timeArr)
  
        
