import time
import board
import json
import _bleio
import binascii
import digitalio
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from adafruit_bluefruit_connect.packet import Packet
from adafruit_circuitplayground import cp

# roba bluetooth
ble = BLERadio()
address = ble.address_bytes
address_str = binascii.hexlify(address).decode("utf-8")
_bleio.adapter.name = "LIGHTPOD-" + address_str[0:4]

uart = UARTService()
advertisement = ProvideServicesAdvertisement(uart)
ledlevel = 0.5


def blink():
    global ledlevel
    for i in range(5):
        cp.pixels.brightness = ledlevel
        cp.pixels.fill((255, 0, 0))
        time.sleep(0.5)
        cp.pixels.fill((0, 0, 0))
        time.sleep(0.5)

def calibration():
    lightlevel = [0,0,0,0,0]
    global ledlevel
    ledlevel = 0.1
    cp.pixels.fill((255,0,0))
    for i in range(4):
        lightlevel[i] = cp.light
    lightlevelMean = meanValue(lightlevel)
    print(lightlevel)
    print("level: " + str(lightlevel) + "BRIGHTNESS: " + str(ledlevel))
    while (lightlevelMean < 150 and ledlevel < 0.9):
        ledlevel = ledlevel + 0.1
        # print(str(ledlevel))
        cp.pixels.brightness = ledlevel
        for i in range(4):
            lightlevel[i] = cp.light
            time.sleep(0.1)
        # time.sleep(0.3)
        # lightlevel = cp.light
        lightlevelMean = meanValue(lightlevel)
        print("level: " + str(lightlevelMean) + "BRIGHTNESS: " + str(ledlevel))
    print("level: " + str(lightlevelMean) + "BRIGHTNESS: " + str(ledlevel))
    cp.pixels.fill((0,0,0))


def insertIntoLightBuffer(value):
    global counter
    global lightbuffer_length
    global lightbuffer_short_len
    global lightbuffer

    counter = counter + 1
    for x in range(lightbuffer_length + lightbuffer_short_len - 1):
        lightbuffer[x] = lightbuffer[x + 1]
    lightbuffer[-1] = value


def insertIntoAccBuffer(x, y, z):
    global counter
    counter = counter + 1
    for i in range(accbuffer_len - 1):
        xaccbuffer[i] = xaccbuffer[i + 1]
        yaccbuffer[i] = yaccbuffer[i + 1]
        zaccbuffer[i] = zaccbuffer[i + 1]
    xaccbuffer[-1] = x
    yaccbuffer[-1] = y
    zaccbuffer[-1] = z


def insertIntoAccBufferShort(x, y, z):
    for i in range(accbuffer_short_len - 1):
        xaccbuffer_short[i] = xaccbuffer_short[i + 1]
        yaccbuffer_short[i] = yaccbuffer_short[i + 1]
        zaccbuffer_short[i] = zaccbuffer_short[i + 1]
    xaccbuffer_short[-1] = x
    yaccbuffer_short[-1] = y
    zaccbuffer_short[-1] = z


def countdown(time_sec):
    while time_sec:
        mins, secs = divmod(time_sec, 60)
        timeformat = "{:02d}:{:02d}".format(mins, secs)
        #print(timeformat, end="\r")
        time.sleep(1)
        time_sec -= 1
    cp.pixels.fill((0, 0, 0))
    #print("stop")


def meanValue(array):
    sum = 0
    for i in range(0, len(array)):
        sum = sum + array[i]
    return sum / len(array)


def lighttreshold(perc):
    if counter > 2*(lightbuffer_length + lightbuffer_short_len):
        m1 = meanValue(lightbuffer[0:lightbuffer_length-1])
        m2 = meanValue(lightbuffer[lightbuffer_length:])
        #print("meanA: "+str(m1))
        #print("meanB: "+str(m2))
        #print((m1,m2))
        diff = abs(m1 - m2)
        if diff > (m1 * perc / 100):
            #print("LIGHT CHANGE DETECTED")
            #print(lightbuffer)
            #print("counter: " + str(counter))
            return True
        else:
            return False


def motiontreshold(perc):
    if counter > accbuffer_len:
        diffx = abs(meanValue(xaccbuffer) - meanValue(xaccbuffer_short))
        diffy = abs(meanValue(yaccbuffer) - meanValue(yaccbuffer_short))
        diffz = abs(meanValue(zaccbuffer) - meanValue(zaccbuffer_short))
        if diffx > (meanValue(xaccbuffer) * perc / 100):
            print("MOTION DETECTED")
            # print(xaccbuffer)
            # print(xaccbuffer_short)
            # print("DIFF X:", diffx)
            return True
        else:
            return False
        if diffy > (meanValue(yaccbuffer) * perc / 100):
            print("MOTION DETECTED")
            #print(yaccbuffer)
            #print(yaccbuffer_short)
            #print("DIFF Y:", diffy)
            return True
        else:
            return False
        if diffz > (meanValue(zaccbuffer) * perc / 100):
            print("MOTION DETECTED")
            #print(zaccbuffer)
            #print(zaccbuffer_short)
            #print("DIFF Z:", diffz)
            return True
        else:
            return False


def readSensors(light, motion, uart):
    global timestop
    global counter
    global lightbuffer_length
    global lightbuffer_short_len
    global lightbuffer

    lightbuffer_length = 50
    lightbuffer_short_len = 4
    lightbuffer = [0 for element in range(lightbuffer_length + lightbuffer_short_len)]
    counter = 0

    while True:
        lightlevel = cp.light
        x, y, z = cp.acceleration
        # print((x, y, z))
        # print(level)
        # print((level,))
        if light:
            insertIntoLightBuffer(lightlevel)
            if lighttreshold(20):
                timestop = time.monotonic()
                delta = (timestop - timeinit)*1000
                cp.pixels.fill((0, 0, 0))
                uart.write("OFF,"+str(delta))
                print("TX: OFF,"+str(delta))
                break
        if motion:
            insertIntoAccBuffer(x, y, z)
            insertIntoAccBufferShort(x, y, z)
            if motiontreshold(1000):
                timestop = time.monotonic()
                delta = (timestop - timeinit)*1000
                cp.pixels.fill((0, 0, 0))
                uart.write("OFF,"+str(delta))
                print("TX: OFF,"+str(delta))
                break

def main():
    global pixelbright
    global lightbuffer_length
    global lightbuffer_short_len
    global lightbuffer
    global lightbuffer_short
    global accbuffer_len
    global xaccbuffer
    global yaccbuffer
    global zaccbuffer
    global accbuffer_short_len
    global xaccbuffer_short
    global yaccbuffer_short
    global zaccbuffer_short
    global timeinit
    global timestop

    ble.start_advertising(advertisement)

    cp.pixels.fill((0, 0, 0))  # Turn off the NeoPixels if they're on!
    lightbuffer_length = 50
    lightbuffer_short_len = 4
    lightbuffer = [0 for element in range(lightbuffer_length + lightbuffer_short_len)]


    accbuffer_len = 30
    xaccbuffer = [0 for element in range(accbuffer_len)]
    yaccbuffer = [0 for element in range(accbuffer_len)]
    zaccbuffer = [0 for element in range(accbuffer_len)]

    accbuffer_short_len = 2
    xaccbuffer_short = [0 for element in range(accbuffer_short_len)]
    yaccbuffer_short = [0 for element in range(accbuffer_short_len)]
    zaccbuffer_short = [0 for element in range(accbuffer_short_len)]


    while not ble.connected:
        pass

    while ble.connected:
        global ledlevel
        cp.red_led = True
        if uart.in_waiting:
            raw_bytes = uart.read(uart.in_waiting)
            text = raw_bytes.decode().strip()
            list = text.split(",")
            print("RX:", text)
            # PROTOCOLLO
            # 0 ON
            # 1 TYPE = {L,M,A}
            # 2 R {255}
            # 3 G {255}
            # 4 B {255}
            if list[0] == "ON":
                # print(time.monotonic_ns)
                timeinit = time.monotonic()
                cp.pixels.brightness = ledlevel
                cp.pixels[2] = (int(list[2]), int(list[3]), int(list[4]))
                cp.pixels[3] = (int(list[2]), int(list[3]), int(list[4]))
                cp.pixels[4] = (int(list[2]), int(list[3]), int(list[4]))
                cp.pixels[5] = (int(list[2]), int(list[3]), int(list[4]))
                cp.pixels[6] = (int(list[2]), int(list[3]), int(list[4]))
                cp.pixels[7] = (int(list[2]), int(list[3]), int(list[4]))
                cp.pixels[8] = (int(list[2]), int(list[3]), int(list[4]))
                cp.pixels[9] = (int(list[2]), int(list[3]), int(list[4]))
                if list[1] == "L":
                    readSensors(True, False, uart)
                if list[1] == "M":
                    readSensors(False, True, uart)
                if list[1] == "A":
                    readSensors(True, True, uart)
            if list[0] == "OFF":
                cp.pixels.fill((0, 0, 0))
            if list[0] == "BLINK":
                blink()
            if list[0] == "CAL":
                calibration()
            #print(list)


while True:
    main()
