# python3

import sys
import os
import time
import datetime
import serial
import binascii

port_CAN = '/dev/ttyUSB0'  #'COM5'
#port_CAN = 'COM3'
port_CAN_baudrate = 115200
log_path = '/media/flash-log/'
#log_path = 'log'
number_of_read_atempt = 50


def open_file(path):
    start_time = datetime.datetime.today()
    #end_time = datetime.datetime(start_time.year, start_time.month, start_time.day, \
    # 23, 59, 59, 999999 )
    end_time = datetime.datetime(start_time.year, start_time.month, start_time.day, \
                                 21, 42, 59, 0)
    log_name = start_time.strftime("%Y-%m-%d_%H-%M-%S")
    log_file = open(os.path.join(path, log_name), 'a')
    return (end_time, log_file)

def init_serial(port, baudrate):
    try:
        ser = serial.Serial(port, baudrate,
                                bytesize=serial.EIGHTBITS,
                                parity=serial.PARITY_NONE,
                                stopbits=serial.STOPBITS_ONE
        )
        ser.close()
        ser.open()

    except (OSError, serial.SerialException):
        sys.stderr.write("Port {} don't work".format(ser.name))
        sys.exit(0)  #need to import sys, otherwise ask if kill program
    return ser

def main_loop(CAN_port, time_end, log_file):
    buffer_string=0
    while (datetime.datetime.today()<time_end):
        n = CAN_port.inWaiting()
        if n != 0:
            buffer_string = CAN_port.read(n)
            temp = str(binascii.hexlify(buffer_string))[2:-1]  #cut "b'" at the begining and "'" at the end
            # command "1100AF" is display as "b'1100AF'"
            pretty_text = ''
            i = 0
            for c in temp:
                if i % 2 == 0:
                    pretty_text = pretty_text + c
                else:
                    pretty_text = pretty_text + c + " "
                i = i + 1
            print(pretty_text)
            log_file.write(time.asctime() + ": " + pretty_text + "\n")
    log_file.close()
    CAN_port.close()
    print("Port {}->CAN is closed.".format(CAN_port.name))

# MAIN LOOP
print("Start")
work_until, file = open_file(log_path)
print("Log will be write into: {}".format(file.name))
print("Work will be terminated at: {}".format(work_until))
ser_CAN = init_serial(port_CAN, port_CAN_baudrate)
print("Port {}->CAN is opened sucessfully.".format(ser_CAN.name))
main_loop(ser_CAN, work_until, file)
print("Finished")

#--------------------------------------
#TODO
#--------------------------------------
#zapis danych co n minut

#--------------------------------------
#DONE
#--------------------------------------
#zamykanie pliku o polnocy

#--------------------------------------	
#KNOW-HOW: wyswietlanie daty i godziny
#--------------------------------------
#temp_dzis = datetime.datetime.today()
#print("data: {}".format(temp_dzis.strftime("%d-%m-%Y")))
#-
#print("test {}".format(datetime.datetime.today().year))
#-	
#teraz = datetime.datetime.today()
#rok = teraz.year
#godzina = teraz.hour
#minuty = teraz.minute
#--------------------------------------