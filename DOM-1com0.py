import time
import sys
import serial

port_CAN = '/dev/ttyUSB1'#'COM5'
port_SATEL = '/dev/ttyUSB0'#COM11'

def transform_data(data):
    if(type(data) == type('String')):
        data = bytearray(data,'ascii')
    return data

def send_to_CAN(command,data):
   print("test")

def read_from_SATEL():
    eol = b'FE0D'
    start = b'FEFE'
    lenstart = len(start)
    leneol = len(eol)
    line = bytearray()
    while True:
        c = ser_SATEL.read(1) #self.ser_SATEL.read(1) 
        if c:
            line += c
            print("Licznik znaków w buforze:",len(line),'\t')

            #print("Znakow: %d \t zawartosc: %d" %{len(line),line})
            if line[-lenstart:] == start:
                #wykryto znacznik poczatku ramki (start),
                #wiec porzucamy to co bylo odebrane wczesniej
                for a in range (0,(len(line)-lenstart)):
                    #print(line)
                    line.pop(0) #wyrzucamy pierwszy element (najstarszy) z bufora odbiorczego
            if line[-leneol:] == eol:
                break
        else:
            break
    return bytes(line)   

#def open_port(port_number):
try:
    ser_SATEL = serial.Serial(
        port=port_SATEL,
        baudrate=19200,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE
        )
    ser_SATEL.close()    
    ser_SATEL.open()    
    print("Port COM->CAN (",ser_SATEL.name,") jest otwarty")
except (OSError, serial.SerialException):
    sys.stderr.write("COM->CAN nie smiga")
    print ("Blad otwarcia portu COM->CAN") 
    sys.exit(0)     #bez sys wywala pytanie czy chcesz zaibic program

i=1
"""
# tutaj nie wiem czemu odbiera tylko pierwszy znak,
# a nie potrafi kolejno ciagu znakow rozpoznac - kolejnych if
while (i==0):
    msg=ser_SATEL.read()
    print(msg)
    if msg == ('F'.encode()):
        print("odebral F")
        if msg ==('E'.encode()):
            print("odebral E")
            if msg == (b'F'):
                print("odebral drugie F")
                i=1
"""
i=0
msg=[]
while (i==0):
    msg=read_from_SATEL()
    print('Ramka:%s'% msg)

#exit(0)        
ser_SATEL.close()



