#!/usr/bin/env python

import sys
import os
import time
import threading
import socket
import serial
import MySQLdb
import binascii

try:
    True
except NameError:
   # True = 1
   # False = 0
   a=1
    
class CanbusReader:
    def __init__(self, serial, mysql, spy=False, spy_serial=False):
        self.serial = serial
        self.mysql = mysql
        self.spy = spy
        self.spy_serial = spy_serial
    
    def initialize(self):
        self.alive = True
        self.thread_read = threading.Thread(target=self.reader)
        self.thread_read.setDaemon(True)
        self.thread_read.setName('CANBUS Input')
        self.thread_read.start()
        self.status_check()
    
    def reader(self):
        buffor = ''
        while self.alive:
            try:
                 data = self.serial.read(1)
                 n = self.serial.inWaiting()
                 if n:
                     data = data + self.serial.read(n)
                 if data:
                     if spy_serial:
                         pretty_text = 'SERIAL:'
                         for c in data: pretty_text = pretty_text + " " + binascii.hexlify(c)
                         sys.stdout.write('%s\n' % pretty_text)
                         sys.stdout.flush() #MSMS? po co flush jeszcze?
                     isSending = True
                     while isSending:
                         data = buffor + data 
                         if len(data) > 12:
                             send_data = data[:12]
                             buffor = data[12:]
                             data = ''
                         elif len(data) == 12:
                             send_data = data;
                             buffor = ''
                             data = ''
                         else:             
                             send_data = '';
                             isSending = False;         
                             buffor = data;
                             break;
                     
                         if len(send_data)>0:
                             if self.spy_serial:
								 #MSMS? czy ten spy_serial to to samo co spy_serial w lini 42 przy if?
                                 pretty_text = 'RX:'
                                 for c in send_data: pretty_text = pretty_text + " " + binascii.hexlify(c)
                                 sys.stdout.write('%s\n' % pretty_text)
                                 sys.stdout.flush()
                             text = ''
                             for c in send_data: text = text + binascii.hexlify(c)
                             self.message_analysis(text)
            except socket.error:#socket.error, msg:
                 sys.stderr.write('Error: %s\n' % msg)
                 break
        self.alive = False
        
    def stop(self):
        if self.alive:
            self.alive = False

    def status_check(self):
        if self.alive:
            for i in range(1,255):
               send_data = chr(16)+chr(128)+chr(254)+chr(254)+chr(255)+chr(255)+chr(0)+chr(i)+chr(255)+chr(255)+chr(255)+chr(255)
			   #
               if spy_serial:
                  pretty_text = 'INITIAL:'
                  for c in send_data: pretty_text = pretty_text + " " + binascii.hexlify(c)
                  sys.stdout.write('%s\n' % pretty_text)
                  sys.stdout.flush()
               self.serial.write(send_data)
               time.sleep(0.02)
            
    def canbus_serial_no(self, item_id, group_id, text):
        try:
            device_id = False
            cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("""SELECT id FROM device WHERE group_id = %s and item_id = %s""", (group_id, item_id))
            result_set = cursor.fetchall()
            for row in result_set:
                device_id = row["id"]
            
            if device_id:
                cursor.execute("""UPDATE device_info SET device_value = %s WHERE device_id = %s and device_attribute = %s """, (str(int(text[12:14],16))+"."+str(int(text[14:15],16))+" rev."+str(int(text[15:16],16)), device_id, 'UNIV_VERSION'))
                cursor.execute("""UPDATE device_info SET device_value = %s WHERE device_id = %s and device_attribute = %s """, (text[16:], device_id, 'PROCESSOR_ID'))
                
            cursor.close()
        except MySQLdb.Error:#MySQLdb.Error, e:
            sys.stdout.write("MySQL: Error %d: %s\n" % (e.args[0], e.args[1]))

        if self.spy:
            sys.stdout.write('RX: %s,%s - Pytanie o numer seryjny. Typ: 0x%s. Univ: %d.%d rev.%d. ID procesora: %sh\n' % (group_id, item_id, text[8:12], int(text[12:14],16),int(text[14:15],16),int(text[15:16],16), text[16:]))
            sys.stdout.flush()        
            
    def canbus_firmware(self, item_id, group_id, text):
        try:
            device_id = False
            cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("""SELECT id FROM device WHERE group_id = %s and item_id = %s""", (group_id, item_id))
            result_set = cursor.fetchall()
            for row in result_set:
                device_id = row["id"] #MSMS? dlaczego indeks w ""
            
            if not device_id:
                if self.spy:
                    sys.stdout.write('Znalazlem nowy modul %s,%s\n' % (group_id, item_id))
                    sys.stdout.flush()
                    
                firm_code = int(text[16:18],16)        
                firm_version = int(text[18:20],16)
                
                device_type_id = False
                channel_counts = False
                if firm_code == 1:
                    device_type_id = 1
                    channel_counts = 6
                if firm_code == 2 and firm_version == 11:
                    device_type_id = 2
                    channel_counts = 6
                if firm_code == 255 and firm_version == 1:
                    device_type_id = 1
                    channel_counts = 6
 
                description = "NEW_" + str(group_id) + "_" + str(item_id);
 
                if self.spy:
                    sys.stdout.write('Odnaleziony modul to %s. Opis: %s. Firmware: %s.%s\n' % (device_type_id, description, firm_code, firm_version))
                    sys.stdout.flush()
 
                if device_type_id:
                    cursor.execute("""INSERT INTO device (device_type_id, description, group_id, item_id) VALUES (%s, %s, %s, %s)""", (device_type_id, description, group_id, item_id))
                    device_id = mysql.insert_id()
                    for channel in range(1, channel_counts+1):
                        cursor.execute("""INSERT INTO device_status (device_id, channel_id) VALUES (%s,%s) """, (device_id, channel))
                    cursor.execute("""INSERT INTO device_info (device_id, device_attribute, device_value) VALUES (%s,%s,%s) """, (device_id, 'TYPE', '0x'+text[8:12]))
                    cursor.execute("""INSERT INTO device_info (device_id, device_attribute, device_value) VALUES (%s,%s,%s) """, (device_id, 'FIRMWARE', str(int(text[12:14],16))+"."+str(int(text[14:16],16))+"."+str(int(text[16:18],16))+"."+str(int(text[18:20],16))))
                    cursor.execute("""INSERT INTO device_info (device_id, device_attribute, device_value) VALUES (%s,%s,%s) """, (device_id, 'BOOTLOADER', str(int(text[20:22],16))+"."+str(int(text[22:24],16))))
                    cursor.execute("""INSERT INTO device_info (device_id, device_attribute, device_value) VALUES (%s,%s,%s) """, (device_id, 'UNIV_VERSION', ""))
                    cursor.execute("""INSERT INTO device_info (device_id, device_attribute, device_value) VALUES (%s,%s,%s) """, (device_id, 'DESCRIPTION', ""))
                    cursor.execute("""INSERT INTO device_info (device_id, device_attribute, device_value) VALUES (%s,%s,%s) """, (device_id, 'PROCESSOR_ID', ""))
                    cursor.execute("""INSERT INTO device_info (device_id, device_attribute, device_value) VALUES (%s,%s,%s) """, (device_id, 'VOLTAGE', ""))
                    
            else:
                cursor.execute("""UPDATE device_info SET device_value = %s WHERE device_id = %s and device_attribute = %s """, ('0x'+text[8:12],device_id, 'TYPE'))
                cursor.execute("""UPDATE device_info SET device_value = %s WHERE device_id = %s and device_attribute = %s """, (str(int(text[12:14],16))+"."+str(int(text[14:16],16))+"."+str(int(text[16:18],16))+"."+str(int(text[18:20],16)), device_id, 'FIRMWARE'))
                cursor.execute("""UPDATE device_info SET device_value = %s WHERE device_id = %s and device_attribute = %s """, (str(int(text[20:22],16))+"."+str(int(text[22:24],16)), device_id, 'BOOTLOADER'))
                
            cursor.close()
        except MySQLdb.Error: # MySQLdb.Error, e:
            sys.stdout.write("MySQL: Error %d: %s\n" % (e.args[0], e.args[1]))
    
        if self.spy:
            sys.stdout.write('RX: %s,%s - Pytanie o wersje firmware. Typ: 0x%s. Wersja: %d.%d.%d.%d. Bootloader: %d.%d\n' % (group_id, item_id, text[8:12], int(text[12:14],16),int(text[14:16],16),int(text[16:18],16),int(text[18:20],16), int(text[20:22],16),int(text[22:24],16)))
            sys.stdout.flush()        

    def canbus_default_id(self, item_id, group_id, text):
        if self.spy:
            sys.stdout.write('RX: %s,%s - Zresetowany adres do domyslnego\n' % (group_id, item_id))
            sys.stdout.flush()        

    def canbus_voltage(self, item_id, group_id, text):
        voltage = 30.5 * int(text[8:12],16) / int('FFC0',16)

        try:
            device_id = False
            cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("""SELECT id FROM device WHERE group_id = %s and item_id = %s""", (group_id, item_id))
            result_set = cursor.fetchall()
            for row in result_set:
                device_id = row["id"]
            
            if device_id:
                cursor.execute("""UPDATE device_info SET device_value = %s WHERE device_id = %s and device_attribute = %s """, (voltage, device_id, 'VOLTAGE'))
                
            cursor.close()
        except MySQLdb.Error:#MySQLdb.Error, e:
            sys.stdout.write("MySQL: Error %d: %s\n" % (e.args[0], e.args[1]))

        if self.spy:
            sys.stdout.write('RX: %s,%s - Pytanie o napiecie zasilania - %6.2fV\n' % (group_id, item_id, voltage))
            sys.stdout.flush()        

    def canbus_description(self, item_id, group_id, text):
        str = ''
        for x in [8,10,12,14,16,18,20,22]:
            str = str + chr(int(text[x:x+2],16))
            
        try:
            device_id = False
            cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("""SELECT id FROM device WHERE group_id = %s and item_id = %s""", (group_id, item_id))
            result_set = cursor.fetchall()
            for row in result_set:
                device_id = row["id"]
            
            if device_id:
                cursor.execute("""SELECT device_value FROM device_info WHERE device_id = %s and device_attribute = %s """, (device_id, 'DESCRIPTION'))
                description = ''
                result_set = cursor.fetchall()
                for row in result_set:
                    description = row['device_value']
                
                if len(description)>15:
                    description = str
                elif len(description)>7:
                    description = description + str
                else:
                    description = str
                
                cursor.execute("""UPDATE device_info SET device_value = %s WHERE device_id = %s and device_attribute = %s """, (description, device_id, 'DESCRIPTION'))
                
            cursor.close()
        except MySQLdb.Error:#, e:
            sys.stdout.write("MySQL: Error %d: %s\n" % (e.args[0], e.args[1]))

            
        if self.spy:
            sys.stdout.write('RX: %s,%s - Pytanie o opis: %s\n' % (group_id, item_id, str))
            sys.stdout.flush()        

    def canbus_id_processor(self, item_id, group_id, text):
        if self.spy:
            sys.stdout.write('RX: %s,%s - Pytanie o id procesora - %s\n' % (group_id, item_id, text[8:12]))
            sys.stdout.flush()        

    def canbus_uptime(self, item_id, group_id, text):
        uptime = int(text[16:18],16)*256*256*256+int(text[18:20],16)*256*256+int(text[20:22],16)*256+int(text[22:24],16)
        if self.spy:
            sys.stdout.write('RX: %s,%s - Pytanie o czas zycia %ds\n' % (group_id, item_id, uptime))
            sys.stdout.flush()

    def canbus_health(self, item_id, group_id, text):
        str_val = ''
        if text[8:10] == '01':
           str_val = str_val + "RXCNT=" + str(int(text[10:12],16)) + ", TXCNT=" + str(int(text[12:14],16)) + ", RXCNTMX=" + str(int(text[14:16],16))
           str_val = str_val + ", TXCNTMAX=" + str(int(text[16:18],16)) + ", CANINTCNT=" + str(int(text[18:20],16)) + ", RXERRCNT=" + str(int(text[20:22],16))
           str_val = str_val + ", TXERRCNT=" + str(int(text[22:24],16))
        elif text[8:10] == '02':
           str_val = str_val + "RXCNTMXE=" + str(int(text[14:16],16)) + ", TXCNTMXE=" + str(int(text[16:18],16)) + ", CANINTCNTE=" + str(int(text[18:20],16))
           str_val = str_val + ", RXERRCNTE=" + str(int(text[20:22],16)) + ", TXERRCNTE=" + str(int(text[22:24],16))        
        if self.spy:
            sys.stdout.write('RX: %s,%s - Pytanie o stan zdrowia. Ramka %s - %s\n' % (group_id, item_id, text[8:10], str_val))
            sys.stdout.flush()
        
    def canbus_error(self, item_id, group_id, text):
        if self.spy:
            sys.stdout.write('RX: %s,%s - Bledna ramka\n' % (group_id, item_id))
            sys.stdout.flush()        

    def canbus_status_button(self, item_id, group_id, data, change):
        channel = int(data[12:14],16)
        status = data[14:16]
        
        try:
            device_id = False
            cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("""SELECT id FROM device WHERE group_id = %s and item_id = %s""", (group_id, item_id))
            result_set = cursor.fetchall()
            for row in result_set:
                device_id = row["id"]
            
            if device_id:
                cursor.execute("""UPDATE device_status SET status = %s WHERE device_id = %s and channel_id = %s """, (int(status,16), device_id, channel))
                
                sensor_id = False
                sensor_channel = False
                sensor_scaler = False
                cursor.execute("""SELECT element_id, element_channel, connection_type FROM connection WHERE device_id = %s and device_channel = %s and element_type='SENSOR'""", (device_id, channel))
                result_set = cursor.fetchall()
                for row in result_set:
                    sensor_id = row["element_id"]
                    sensor_channel = row["element_channel"]
                    sensor_scaler = row["connection_type"]

                if sensor_id:
                    if sensor_scaler == 'NO':
                       cursor.execute("""UPDATE sensor_status SET status = %s WHERE sensor_id = %s and channel_id = %s """, (255-int(status,16), sensor_id, sensor_channel))
                    else:                    
                       cursor.execute("""UPDATE sensor_status SET status = %s WHERE sensor_id = %s and channel_id = %s """, (int(status,16), sensor_id, sensor_channel))
                    
            cursor.close()
        except MySQLdb.Error:#, e:
            sys.stdout.write("MySQL: Error %d: %s\n" % (e.args[0], e.args[1]))
            
        if self.spy:
            if change:
                if status == 'ff':
                    sys.stdout.write('RX: %s,%s - Zmiana stanu przycisku dla kanalu %d - Przycisk wcisniety.\n' % (group_id, item_id, channel))
                else:
                    sys.stdout.write('RX: %s,%s - Zmiana stanu przycisku dla kanalu %d - Przycisk rozlaczony.\n' % (group_id, item_id, channel))
            else:
                if status == 'ff':
                    sys.stdout.write('RX: %s,%s - Status przycisku dla kanalu %d - Przycisk wcisniety.\n' % (group_id, item_id, channel))
                else:
                    sys.stdout.write('RX: %s,%s - Status przycisku dla kanalu %d - Przycisk rozlaczony.\n' % (group_id, item_id, channel))
            sys.stdout.flush()        

    def canbus_status_relay(self, item_id, group_id, data, change):
        channel = data[12:14]
        status = data[14:16]
        instr = data[18:22]
        timmer = data[22:24]

        try:
            device_id = False
            cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("""SELECT id FROM device WHERE group_id = %s and item_id = %s""", (group_id, item_id))
            result_set = cursor.fetchall()
            for row in result_set:
                device_id = row["id"]
            
            if device_id:
                cursor.execute("""UPDATE device_status SET status = %s WHERE device_id = %s and channel_id = %s """, (int(status,16), device_id, channel))
                
                actor_id = False
                actor_channel = False
                actor_scaler = False
                cursor.execute("""SELECT element_id, element_channel, connection_type FROM connection WHERE device_id = %s and device_channel = %s and element_type='ACTOR'""", (device_id, channel))
                result_set = cursor.fetchall()
                for row in result_set:
                    actor_id = row["element_id"]
                    actor_channel = row["element_channel"]
                    actor_scaler = row["connection_type"]

                if actor_id:
                    if actor_scaler == 'NO':
                       cursor.execute("""UPDATE actor_status SET status = %s WHERE actor_id = %s and channel_id = %s """, (255-int(status,16), actor_id, actor_channel))
                    else:                    
                       cursor.execute("""UPDATE actor_status SET status = %s WHERE actor_id = %s and channel_id = %s """, (int(status,16), actor_id, actor_channel))
                    
            cursor.close()
        except MySQLdb.Error:#, e:
            sys.stdout.write("MySQL: Error %d: %s\n" % (e.args[0], e.args[1]))
            
        if self.spy:
            if change:
                if status == 'ff':
                    sys.stdout.write('RX: %s,%s - Zmiana stanu przekaznika dla kanalu %s - Przekaznik wlaczony. Instrukcja: %s. Timer: %s.\n' % (group_id, item_id, channel, instr, timmer))
                else:
                    sys.stdout.write('RX: %s,%s - Zmiana stanu przekaznika dla kanalu %s - Przekaznik wylaczony. Instrukcja: %s. Timer: %s.\n' % (group_id, item_id, channel, instr, timmer))
            else:
                if status == 'ff':
                    sys.stdout.write('RX: %s,%s - Status przekaznika dla kanalu %s - Przekaznik wlaczony. Instrukcja: %s. Timer: %s.\n' % (group_id, item_id, channel, instr, timmer))
                else:
                    sys.stdout.write('RX: %s,%s - Status przekaznika dla kanalu %s - Przekaznik wylaczony. Instrukcja: %s. Timer: %s.\n' % (group_id, item_id, channel, instr, timmer))
            sys.stdout.flush()        

    def canbus_status_it(self, item_id, group_id, data):
        code = data[12:14]
        address = data[14:16]
        instr = data[16:18]
        if self.spy:
            if code < '80':
                sys.stdout.write('RX: %s,%s - Odbiornik podczerwieni odebral - Rodzaj kodu %s, Adres %s, Rozkaz %s.\n' % (group_id, item_id, code, address, instr))
            else:
                sys.stdout.write('RX: %s,%s - Odbiornik podczerwieni odebral - Rodzaj kodu %s, Adres %s, Rozkaz %s, Koniec nadawania.\n' % (group_id, item_id, code-'80', address, instr))        
            sys.stdout.flush()        

    def canbus_status_temp(self, item_id, group_id, data, change):
        if self.spy:
            sys.stdout.write('RX: %s,%s - %s - Status czujnik temperatury\n' % (group_id, item_id, data[8:]))
            sys.stdout.flush()        

    def canbus_status_dimmer(self, item_id, group_id, data, change):
        channel = data[12:14]
        status = data[14:16]
        instr = data[18:22]
        timmer = data[22:24]

        try:
            device_id = False
            cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("""SELECT id FROM device WHERE group_id = %s and item_id = %s""", (group_id, item_id))
            result_set = cursor.fetchall()
            for row in result_set:
                device_id = row["id"]
            
            if device_id:
                cursor.execute("""UPDATE device_status SET status = %s WHERE device_id = %s and channel_id = %s """, (int(status,16), device_id, channel))
                
                actor_id = False
                actor_channel = False
                actor_scaler = False
                cursor.execute("""SELECT element_id, element_channel, connection_type FROM connection WHERE device_id = %s and device_channel = %s and element_type='ACTOR'""", (device_id, channel))
                result_set = cursor.fetchall()
                for row in result_set:
                    actor_id = row["element_id"]
                    actor_channel = row["element_channel"]
                    actor_scaler = row["connection_type"]

                if actor_id:
                    if actor_scaler == 'NO':
                       cursor.execute("""UPDATE actor_status SET status = %s WHERE actor_id = %s and channel_id = %s """, (255-int(status,16), actor_id, actor_channel))
                    else:                    
                       cursor.execute("""UPDATE actor_status SET status = %s WHERE actor_id = %s and channel_id = %s """, (int(status,16), actor_id, actor_channel))
                    
            cursor.close()
        except MySQLdb.Error:#, e:
            sys.stdout.write("MySQL: Error %d: %s\n" % (e.args[0], e.args[1]))

        if self.spy:
            if change:
                sys.stdout.write('RX: %s,%s - Zmiana stanu sciemniacza dla kanalu %s - Wartosc nastawy: %s. Instrukcja: %s. Timer: %s.\n' % (group_id, item_id, channel, status, instr, timmer))
            else:
                sys.stdout.write('RX: %s,%s - Status sciemniacza dla kanalu %s - Wartosc nastawy: %s. Instrukcja: %s. Timer: %s.\n' % (group_id, item_id, channel, status, instr, timmer))
            sys.stdout.flush()        
            
    def canbus_status_blind(self, item_id, group_id, data, change):
        channel = data[12:14]
        status = data[14:16]
        direction = data[16:18]
        instr = data[18:22]
        timmer = data[22:24]
        if self.spy:
            if change:
                if direction == '00':
                     sys.stdout.write('RX: %s,%s - Zmiana stanu rolety dla kanalu %s - Stan rolety %s. Kierunek: zatrzymana. Instrukcja: %s. Timer: %s.\n' % (group_id, item_id, channel, status, instr, timmer))
                elif direction == '01':
                     sys.stdout.write('RX: %s,%s - Zmiana stanu rolety dla kanalu %s - Stan rolety %s. Kierunek: do dolu. Instrukcja: %s. Timer: %s.\n' % (group_id, item_id, channel, status, instr, timmer))
                elif direction == '02':
                     sys.stdout.write('RX: %s,%s - Zmiana stanu rolety dla kanalu %s - Stan rolety %s. Kierunek: do gory. Instrukcja: %s. Timer: %s.\n' % (group_id, item_id, channel, status, instr, timmer))
            else:
                if direction == '00':
                     sys.stdout.write('RX: %s,%s - Stan rolety dla kanalu %s - Stan rolety %s. Kierunek: zatrzymana. Instrukcja: %s. Timer: %s.\n' % (group_id, item_id, channel, status, instr, timmer))
                elif direction == '01':
                     sys.stdout.write('RX: %s,%s - Stan rolety dla kanalu %s - Stan rolety %s. Kierunek: do dolu. Instrukcja: %s. Timer: %s.\n' % (group_id, item_id, channel, status, instr, timmer))
                elif direction == '02':
                     sys.stdout.write('RX: %s,%s - Stan rolety dla kanalu %s - Stan rolety %s. Kierunek: do gory. Instrukcja: %s. Timer: %s.\n' % (group_id, item_id, channel, status, instr, timmer))
            sys.stdout.flush()        

    def canbus_status_rgb(self, item_id, group_id, data, change):
        channel = data[12:14]
        status = data[14:16]
        status2 = data[16:18]
        instr = data[18:24]
        if self.spy:
            if change:
                sys.stdout.write('RX: %s,%s : Zmiana stanu sterownika led dla kanalu %s - Stan 1 %s. Stan 2 %s. Instrukcja: %s.\n' % (group_id, item_id, channel, status, status2, instr))
            else:
                sys.stdout.write('RX: %s,%s : Stan sterownika led dla kanalu %s - Stan 1 %s. Stan 2 %s. Instrukcja: %s.\n' % (group_id, item_id, channel, status, status2, instr))
            sys.stdout.flush()        
            
            
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
                elif command == '105':
                    self.canbus_firmware(item_id, group_id, text)
                elif command == '106':
                    self.canbus_firmware(item_id, group_id, text)
                elif command == '107':
                    self.canbus_default_id(item_id, group_id, text)
                elif command == '10b':
                    self.canbus_voltage(item_id, group_id, text)
                elif command == '10c':
                    self.canbus_voltage(item_id, group_id, text)
                elif command == '10d':
                    self.canbus_description(item_id, group_id, text)
                elif command == '10e':
                    self.canbus_description(item_id, group_id, text)
                elif command == '10f':
                    self.canbus_id_processor(item_id, group_id, text)
                elif command == '110':
                    self.canbus_id_processor(item_id, group_id, text)
                elif command == '113':
                    self.canbus_uptime(item_id, group_id, text)
                elif command == '115':
                    self.canbus_health(item_id, group_id, text)
                elif command == '1f0':
                    self.canbus_error(item_id, group_id, text)
                elif command == '1f1':
                    self.canbus_error(item_id, group_id, text)
                elif command == '301':
                    self.canbus_status_button(item_id, group_id, text, False)
                elif command == '302':
                    self.canbus_status_relay(item_id, group_id, text, False)
                elif command == '304':
                    self.canbus_status_temp(item_id, group_id, text, False)
                elif command == '306':
                    self.canbus_status_dimmer(item_id, group_id, text, False)
                elif command == '307':
                    self.canbus_status_blind(item_id, group_id, text, False)
                elif command == '308':
                    self.canbus_status_rgb(item_id, group_id, text, False)
            if text[3]=="0":
                command = text[:3]
                if command == '301':
                    self.canbus_status_button(item_id, group_id, text, True)
                elif command == '302':
                    self.canbus_status_relay(item_id, group_id, text, True)
                elif command == '303':
                    self.canbus_status_it(item_id, group_id, text)
                elif command == '304':
                    self.canbus_status_temp(item_id, group_id, text, True)
                elif command == '306':
                    self.canbus_status_dimmer(item_id, group_id, text, True)
                elif command == '307':
                    self.canbus_status_blind(item_id, group_id, text, True)
                elif command == '308':
                    self.canbus_status_rgb(item_id, group_id, text, True)
                

class CanbusWriter:    
    def __init__(self, serial_instance, socket, spy=False, spy_socket=False):
        self.serial = serial_instance
        self.socket = socket
        self.spy = spy
        self.spy_socket = spy_socket

    def initialize(self):
        self.alive = True
        self.writer()

    def writer(self):
        while self.alive:
            try:
                data = self.socket.recv(20)
                if not data:
                   break
                commands = data.split('\r\n')   
                for comm in commands:               
                    sys.stdout.flush()   
                    if self.spy_socket:
                       sys.stdout.write('SOCKET: %s\n' % comm)
                       sys.stdout.flush()
                    send_data = self.message_analysis(comm)
                    self.serial.write(send_data)
                    if self.spy_socket:
                       pretty_text = 'TX:'
                       for c in send_data:
                            pretty_text = pretty_text + " " + binascii.hexlify(c)
                       sys.stdout.write('%s\n' % pretty_text)
                       sys.stdout.flush()
                    time.sleep(0.01)
            except socket.error:#, msg:
                sys.stderr.write('ERROR %s\n' % msg)
                break
        self.alive = False
        
    def message_analysis(self, command): 
        data = ''       
        instr = command[:3]
        group_id = command[3:6]
        item_id = command[6:9]
        if len(command)>9:
            data = command[9:]
            
        if group_id.isdigit() and item_id.isdigit():                    
            group_id = int(group_id)
            item_id = int(item_id)
            if instr == '101':
               if self.spy:
                   sys.stdout.write('TX: %s,%s - Restart (grupa)\n' % (group_id, item_id))
                   sys.stdout.flush()
               return chr(16)+chr(16)+chr(254)+chr(254)+chr(255)+chr(255)+chr(item_id)+chr(group_id)+chr(255)+chr(255)+chr(255)+chr(255)
            elif instr == '102':
               if self.spy:
                   sys.stdout.write('TX: %s,%s - Restart\n' % (group_id, item_id))
                   sys.stdout.flush()
               return chr(16)+chr(32)+chr(254)+chr(254)+chr(255)+chr(255)+chr(item_id)+chr(group_id)+chr(255)+chr(255)+chr(255)+chr(255)
            elif instr == '103':
               if self.spy:
                   sys.stdout.write('TX: %s,%s - Numer seryjny (grupa)\n' % (group_id, item_id))
                   sys.stdout.flush()
               return chr(16)+chr(48)+chr(254)+chr(254)+chr(255)+chr(255)+chr(item_id)+chr(group_id)+chr(255)+chr(255)+chr(255)+chr(255)
            elif instr == '104':
               if self.spy:
                   sys.stdout.write('TX: %s,%s - Numer seryjny\n' % (group_id, item_id))
                   sys.stdout.flush()
               return chr(16)+chr(64)+chr(254)+chr(254)+chr(255)+chr(255)+chr(item_id)+chr(group_id)+chr(255)+chr(255)+chr(255)+chr(255)
            elif instr == '105':
               if self.spy:
                   sys.stdout.write('TX: %s,%s - Wersja firmware (grupa)\n' % (group_id, item_id))
                   sys.stdout.flush()
               return chr(16)+chr(80)+chr(254)+chr(254)+chr(255)+chr(255)+chr(item_id)+chr(group_id)+chr(255)+chr(255)+chr(255)+chr(255)
            elif instr == '106':
               if self.spy:
                   sys.stdout.write('TX: %s,%s - Wersja firmware \n' % (group_id, item_id))
                   sys.stdout.flush()
               return chr(16)+chr(96)+chr(254)+chr(254)+chr(255)+chr(255)+chr(item_id)+chr(group_id)+chr(255)+chr(255)+chr(255)+chr(255)
            elif instr == '107':
               if self.spy:
                   sys.stdout.write('TX: %s,%s - Wyzeruj do domyslnego adres\n' % (group_id, item_id))
                   sys.stdout.flush()
               return chr(16)+chr(112)+chr(254)+chr(254)+chr(255)+chr(255)+chr(item_id)+chr(group_id)+chr(255)+chr(255)+chr(255)+chr(255)
            elif instr == '108':
               if self.spy:
                   sys.stdout.write('TX: %s,%s - Status (grupa)\n' % (group_id, item_id))
                   sys.stdout.flush()
               return chr(16)+chr(128)+chr(254)+chr(254)+chr(255)+chr(255)+chr(item_id)+chr(group_id)+chr(255)+chr(255)+chr(255)+chr(255)
            elif instr == '109':
               if self.spy:
                   sys.stdout.write('TX: %s,%s - Status\n' % (group_id, item_id))
                   sys.stdout.flush()
               return chr(16)+chr(144)+chr(254)+chr(254)+chr(255)+chr(255)+chr(item_id)+chr(group_id)+chr(255)+chr(255)+chr(255)+chr(255)
            elif instr == '10a':
               if self.spy:
                   sys.stdout.write('TX: %s,%s - Sterowanie manualne. Instrukcja %s\n' % (group_id, item_id, data))
                   sys.stdout.flush()
               return chr(16)+chr(160)+chr(254)+chr(254)+chr(255)+chr(255)+chr(item_id)+chr(group_id)+chr(255)+chr(int(data[:3]))+chr(int(data[3:6]))+chr(int(data[6:9]))        
            elif instr == '10b':
               if self.spy:
                   sys.stdout.write('TX: %s,%s - Stan napiecia (grupa)\n' % (group_id, item_id))
                   sys.stdout.flush()
               return chr(16)+chr(176)+chr(254)+chr(254)+chr(255)+chr(255)+chr(item_id)+chr(group_id)+chr(255)+chr(255)+chr(255)+chr(255)
            elif instr == '10c':
               if self.spy:
                   sys.stdout.write('TX: %s,%s - Stan napiecia\n' % (group_id, item_id))
                   sys.stdout.flush()
               return chr(16)+chr(192)+chr(254)+chr(254)+chr(255)+chr(255)+chr(item_id)+chr(group_id)+chr(255)+chr(255)+chr(255)+chr(255)
            elif instr == '10d': 
               if self.spy:
                   sys.stdout.write('TX: %s,%s - Opis (grupa)\n' % (group_id, item_id))
                   sys.stdout.flush()
               return chr(16)+chr(208)+chr(254)+chr(254)+chr(255)+chr(255)+chr(item_id)+chr(group_id)+chr(255)+chr(255)+chr(255)+chr(255)
            elif instr == '10e': 
               if self.spy:
                   sys.stdout.write('TX: %s,%s - Opis\n' % (group_id, item_id))
                   sys.stdout.flush()
               return chr(16)+chr(224)+chr(254)+chr(254)+chr(255)+chr(255)+chr(item_id)+chr(group_id)+chr(255)+chr(255)+chr(255)+chr(255)
            elif instr == '10f': 
               if self.spy:
                   sys.stdout.write('TX: %s,%s - ID procesora (grupa)\n' % (group_id, item_id))
                   sys.stdout.flush()
               return chr(16)+chr(240)+chr(254)+chr(254)+chr(255)+chr(255)+chr(item_id)+chr(group_id)+chr(255)+chr(255)+chr(255)+chr(255)
            elif instr == '110': 
               if self.spy:
                   sys.stdout.write('TX: %s,%s - ID procesora\n' % (group_id, item_id))
                   sys.stdout.flush()
               return chr(17)+chr(0)+chr(254)+chr(254)+chr(255)+chr(255)+chr(item_id)+chr(group_id)+chr(255)+chr(255)+chr(255)+chr(255)
            elif instr == '113': 
               if self.spy:
                   sys.stdout.write('TX: %s,%s - Uptime\n' % (group_id, item_id))
                   sys.stdout.flush()
               return chr(17)+chr(48)+chr(254)+chr(254)+chr(255)+chr(255)+chr(item_id)+chr(group_id)+chr(255)+chr(255)+chr(255)+chr(255)
            elif instr == '115': 
               if self.spy:
                   sys.stdout.write('TX: %s,%s - Stan zdrowia\n' % (group_id, item_id))
                   sys.stdout.flush()
               return chr(17)+chr(80)+chr(254)+chr(254)+chr(int(data[:3]))+chr(255)+chr(item_id)+chr(group_id)+chr(255)+chr(255)+chr(255)+chr(255)
        return ''    
        

    def stop(self):
        if self.alive:
            self.alive = False

if __name__ == '__main__':

    port = 'COM5'		#MSMS20141209 '/dev/ttyS1'
    baudrate = '115200'

    spy = True
    spy_serial = True
    spy_socket = True

    net_port = 7777
	
	
    sql_host = '192.168.1.136'
    sql_user = 'domomatik'
    sql_pass = 'raptus1'
    sql_db   = 'domomatik_central'
	#<\>MSMS20141209
	
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = baudrate
    ser.parity = 'N'
    ser.rtscts = None
    ser.xonxoff = None
    ser.timeout = 1
    
    sys.stderr.write("\n\n\n------------------------------\n")
    sys.stderr.write("     CANBUS GATEWAY v.0.1\n")
    sys.stderr.write("SERIAL : %s %s,%s,%s,%s\n" % (ser.portstr, ser.baudrate, 8, ser.parity, 1))
    sys.stderr.write("NET    : localhost:%s\n" % net_port)
    sys.stderr.write("DB     : %s %s %s\n" % (sql_host, sql_user, sql_db))
    sys.stderr.write("------------------------------\n\n\n")

    try:
        ser.open()
    except serial.SerialException:#, e:
        sys.stderr.write("Could not open serial port %s: %s\n" % (ser.portstr, e))
        sys.exit(1)

	#<>MSMS20141209
    try:
        mysql = MySQLdb.connect(host = sql_host, user = sql_user, passwd = sql_pass, db = sql_db)
    except MySQLdb.Error:#, e:
        sys.stderr.write("Could not open MySQL connection. Error %d: %s" % (e.args[0], e.args[1]))
        sys.exit(1)
	#<\>MSMS20141209
        
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind( ('', net_port) )
    srv.listen(1)

    if spy == False:
       spy_serial = False
       spy_socket = False
    
    r = CanbusReader(
        ser,
        mysql,
        spy,
        spy_serial,
    )
    r.initialize()
    
    while True:
        try:
             sys.stderr.write("Waiting for connection on %s...\n" % net_port)
             #MSMS? przypisanie do dwóch zmiennych?
             connection, addr = srv.accept()
             sys.stderr.write('Connected by %s\n' % (addr,))
             r = CanbusWriter(
                 ser,
                 connection,
                 spy,
                 spy_socket,
             )
             r.initialize()
             if spy: sys.stdout.write('\n')
             sys.stderr.write('Disconnected\n')
             connection.close()
        except KeyboardInterrupt:
             break;
        except socket.error:#, msg:
             sys.stderr.write('ERROR %s\n' % msg)

    mysql.close()
    sys.stderr.write('\n--- exit ---\n')
