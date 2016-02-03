#!/usr/bin/env python
# -*- coding: utf-8 -*-
# python2

import sys
import os
import time
import threading
import socket
import serial
import binascii

Debug = True
satel_read_command = "FEFE00D7E2FE0D"
satel_start = b'FEFE'
satel_stop = b'FE0D'

try:
    True
except NameError:
    True = 1
    False = 0
    
class SatelInterface:
    def __init__(self, serial, spy=False, spy_serial=False):
        self.serial = serial
        self.spy = spy
        self.spy_serial = spy_serial
    
    def initialize(self):
        self.alive = True
        self.thread_read = threading.Thread(target=self.reader(satel_read_command, satel_start, satel_stop))
        self.thread_read.setDaemon(True)
        self.thread_read.setName('Satel Input')
        self.thread_read.start()
    
    def reader(self, command, start, stop):
        #line = bytearray()
        buffor=''
        recived_msg=False
        isReceving=False
        if Debug: print("\nSatelInterface.reader initialization")
        while self.alive:
            #wyslanie komendy do satela inicjalizujacej odczyt
            self.serial.write(command)
            #print(binascii.hexlify(command[0]))
            print("Send command to satel:",command)

            #odbior odpowiedzi od satela
            print("Start reading from satel:")
            isReceving = True
            licznik=0
            data=''
            while isReceving:
                data = data + self.serial.read(1)
                n = self.serial.inWaiting()
                if n:
                    data = data + self.serial.read(n)
                buffor = buffor + data
                if Debug:
                    if len(data)>0: print('Recieved data:\n',data)
                if Debug:
                    if len(buffor)>0: print("Buffered data:\n",buffor)
                data = ''
                #self.frame_catcher(dat a, start, stop)
                if (len(buffor)>len(start)):
                    print('analiza')
                    a=0
                    b=0
                    c=0
                    #szukamy pierwszy znacznik startu
                    for a in range(0,len(buffor)-len(start)):
                        if buffor[a:a+len(start)]==start:
                            #szukamy drugiego znacznika startu
                            for b in range(a+1,len(buffor)-len(start)):
                                if buffor[b:b+len(start)]==start:
                                    #sprawdzamy czy pomiedzy znacznikami startu byl znacznik konca
                                    for c in range(a,b):
                                        if buffor[c:c+len(stop)]==stop:
                                            msg=buffor[a:c+len(stop)]
                                            print('znaleziona wiadomosc:',msg)
                                            buffor=buffor[c+len(stop):]
                                            break
                                        else:
                                            if c==b:
                                                buffor=buffor[c:]
                            print("Buffered data after cut:\n",buffor)
                    
    def frame_catcher(self, data, start, stop):
        buffor = buffor + data
        print(buffor)
        temp=''
        a=0
        for a in range (0,len(data)-len(start)):
            if data[a:a+len(start)]==start:
                #Znaleziony pierwszy znacznik startu w ciagu
                print("wykryto 1 znacznik poczatku")
                data=data[a:] #usuwamy to co bylo przed znacznikiem startu
                b=1
                while(b<=(len(data)-len(start))):
                    if data[b:b+len(stop)]==stop:
                        msg=data[a:b+len(stop)]
                        data=data[b+len(stop):]
                        a=0
                        break
                    if data[b:b+len(start)]==start:
                        data=data[b:]
                        a=0
                        break
                if data:
                    bufor = bufor + data
                    print("Bufor:",bufor)
                if msg:
                    print("odebrana wiadomosc to:",msg)
                if msg:
                    print("Odebrana ramka:",msg)
                    if len(msg)>0:
                        if self.spy_serial:
                            pretty_text = 'SATEL_RX:'
                            for c in msg: pretty_text = pretty_text + " " + binascii.hexlify(c)
                            sys.stdout.write('%s\n' % pretty_text)
                            sys.stdout.flush()
                        text = ''
                        for c in msg: text = text + binascii.hexlify(c)
                        self.message_analysis(text)
                break
        self.alive = False

    def message_analysis(self, text):
        if len(text)==24:#MSMS? nie sprawdzamy czy nie przyszła cała ramka, albo co jak przyjdzie przesunieta?
            item_id = int(text[4:6],16)
            group_id = int(text[6:8],16)
            if text[3]=="1":
                command = text[:3]
                if command == '103':
                    self.canbus_serial_no(item_id, group_id, text)
                elif command == '104':
                    self.canbus_serial_no(item_id, group_id, text)
                elif command == '308':
                    self.canbus_status_rgb(item_id, group_id, text, False)
            if text[3]=="0":
                command = text[:3]
                if command == '301':
                    self.canbus_status_button(item_id, group_id, text, True)
                elif command == '302':
                    self.canbus_status_relay(item_id, group_id, text, True)
                elif command == '308':
                    self.canbus_status_rgb(item_id, group_id, text, True)
                
        if self.alive:
            self.alive = False

if __name__ == '__main__':

    port = '/dev/ttyUSB0'#'COM5'#'/dev/ttyS1'
    baudrate = '19200'

    spy = True
    spy_serial = True
    spy_socket = True

    ser = serial.Serial()
    ser.port = port
    ser.baudrate = baudrate
    ser.parity = 'N'
    ser.rtscts = None
    ser.xonxoff = None
    ser.timeout = 1
     
    sys.stderr.write("\n------------------------------\n")
    sys.stderr.write("SATEL-CAN GATEWAY v.0.1\n")
    sys.stderr.write("SERIAL : %s %s,%s,%s,%s\n" % (ser.portstr, ser.baudrate, 8, ser.parity, 1))
    sys.stderr.write("------------------------------\n")

    try:
        ser.open()
        ser.write("Port has been opened successfully.\n")
    except serial.SerialException: #serial.SerialException, e:
        sys.stderr.write("Could not open serial port %s: %s\n" % (ser.portstr, e))
        sys.exit(1)

    if spy == False:
       spy_serial = False
       spy_socket = False
    
    r = SatelInterface(
        ser,
        spy,
        spy_serial,
    )
    r.initialize()
    
    while True:
        try:
            a=1
            if (SatelInterface==False):
                a=2
                # print("uruchamiam ponownie")
                #r.initialize()        
        except KeyboardInterrupt:
            break;
    sys.stderr.write('\n--- exit ---\n')
