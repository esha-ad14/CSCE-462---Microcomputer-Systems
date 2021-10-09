import time
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn 

#turn in
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D22)
mcp = MCP.MCP3008(spi, cs)
chan0 = AnalogIn(mcp, MCP.P0)

def dataGathering():
    voltArr = []
    timeArr = []
    startT = time.time()
    while time.time() - startT < 1:
        voltArr.append(chan0.voltage)
        timeArr.append(time.time()-startT)    
    smoothVolt = []
    smoothVolt.append(voltArr[0])
    for i in range(1, len(voltArr)-1): #
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
    numMin = 0
    numMax = 0
    tolerance = (max-min) * 0.1 
    for i in range(size): 
        if max - voltArr[i] < tolerance:
            numMax = numMax + 1
        elif voltArr[i] - min < tolerance:
            numMin = numMin + 1
    if numMin + numMax > (size * 0.8): 
        print("Square")
        squareFreq(rawVoltageList, timeArr, min, max)
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
                fluctuation = fluctuation + 1
                if (fluctuation >= 5): 
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
                if (fluctuation >= 5): 
                    if (start == -1):
                        start = i-1 - fluctuation
                        side = 0
                    else:
                        end = i-1 - fluctuation
                        break
            else:
                fluctuation = 0
    
    for i in range(0, end):
        edgeArr.append(voltArr[i-1]-voltArr[i])
      
    sum = 0
    #print('len edge arr',len(edgeArr))
    #obtain average change between points
    for i in range(len(edgeArr)):
        sum = sum + edgeArr[i]
        #print(sum, "sum")
#     print(len(edgeArr))
    #IncrAvg = sum / len(edgeArr)
    
    IncrAvg = sum / 3
    #print("incravg", IncrAvg)
    #count the number of changes in two consecutive points that equal the average for the edgeArr
    nIncrAvg = 0
    tolerance = (max-min) * 0.075 #tolerance to account for noise (experimentally determined)
    #for i in range(len(edgeArr)):
    for i in range(len(edgeArr)):
        if abs(IncrAvg - edgeArr[i]) < tolerance:
            nIncrAvg = nIncrAvg + 1
            #print('nIncrAvg middle', nIncrAvg)
    print("val nincravg",nIncrAvg)
    print('len of edgearr',len(edgeArr))
    i f (nIncrAvg < len(edgeArr) * 0.5): #and ((nIncrAvg!=0) and (len(edgeArr)!=0)): #if 50% (experimentally determined) of the increases were equal to the average it is a triangle
    if ((nIncrAvg!=0) and (len(edgeArr)!=0)):
        if((len(edgeArr) / (nIncrAvg)) < 3):
           print("Triangle")
            sinTriangleFreq(voltArr, timeArr, min, max)
        else:
            print("Sin")
           sinTriangleFreq(voltArr, timeArr, min, max)
    else:
     #   print("Sin")
      #  sinTriangleFreq(voltArr, timeArr, min, max)
   
    print('--------------')

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
        print(minTime)
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
  
        