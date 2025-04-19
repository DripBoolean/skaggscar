'''
picobot_api functions:
    picobot_api.setLedColor(led,r,g,b):
        led=[0..7]
        r=[0..255]
        g=[0..255]
        b=[0..255]
        return: None
    picobot_api.playTone(freq,dur):
        freq=[1..20000]
        dur=[0.0 ...] (in seconds)
        return: None
    picobot_api.setMotorPower1(power):
        power=[-100.0...100.0]
        return: None
    picobot_api.setMotorPower2(power)
        power=[-100.0...100.0]
        return: None
    readEncoder1()
        return: int
    readEncoder2()
        return: int
    resetEncoder1()
        return: None
    resetEncoder2()
        return: None
    readButtons()
        return: int
    ping():
        return: [True,False]
'''

import serial

portOpen=False
port=None

def init():
    global portOpen,port
    portOpen=False
    try:
        port=serial.Serial("/dev/ttyACM0",115200,timeout=0.2)
        portOpen=True
    except:
        pass

    if portOpen==False:
        try:
            port=serial.Serial("/dev/ttyACM1",115200,timeout=0.2)
            portOpen=True
        except:
            pass
    
    return portOpen

def setLedColor(led,r,g,b):
    port.write(f"setLedColor,{led},{r},{g},{b}\r\n".encode("utf-8"))
    
def playTone(freq,dur):
    port.write(f"playTone,{freq},{dur}\r\n".encode("utf-8"))

def setMotorPower1(power):
    port.write(f"setMotorPower1,{power}\r\n".encode("utf-8"))
    
def setMotorPower2(power):
    port.write(f"setMotorPower2,{power}\r\n".encode("utf-8"))
    
def readEncoder1():
    port.write("readEncoder1\r\n".encode("utf-8"))
    line=port.readline()
    try:
        value=int(line)
    except:
        value=None
    return value

def readEncoder2():
    port.write("readEncoder2\r\n".encode("utf-8"))
    line=port.readline()
    try:
        value=int(line)
    except:
        value=None
    return value

def resetEncoder1():
    port.write("resetEncoder1\r\n".encode("utf-8"))
    
def resetEncoder2():
    port.write("resetEncoder2\r\n".encode("utf-8"))

def readButtons():
    port.write("readButtons\r\n".encode("utf-8"))
    line=port.readline()
    try:
        value=int(line)
    except:
        value=None
    return value

def ping():
    port.write("ping\r\n".encode("utf-8"))
    line=port.readline()
    try:
        value=bool(line)
    except:
        value=False
    return value

#init()
