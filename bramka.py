import serial
import sys
import binascii

CAN_port = 'COM6'
CAN_baudrate = '9600'
SAT_port = 'COM7'
SAT_baudrate = '9600'
sat_read_command = b"FEFE00D7E2FE0D"
sat_start = b'FEFE'
sat_stop = b'FE0D'


def open_serial(port, baudrate, parity, stop_bits, byte_size, timeout, description):
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = baudrate
    ser.parity = parity
    ser.stopbits  = stop_bits
    ser.bytesize  = byte_size
    ser.timeout  = timeout
    ser.close()
    try:
        ser.open()
        sys.stderr.write("Port {} ({},{},{},{},{}) has been opened successfully.\n".format(description, ser.name, ser.baudrate, 8, ser.parity, 1))
    except IOError :#serial.SerialException: #serial.SerialException, e: #
        sys.stderr.write("Could not open port {}: {}\n".format(ser.name))
        sys.exit(1)
    return(ser)

def send_command_in_hex(ser, command):
    text = ''
    for c in command:
        text = text + binascii.hexlify(c)
    ser.write(text)

def Initialization():
    a=1
    ser_CAN = open_serial(CAN_port, CAN_baudrate, serial.PARITY_NONE, serial.STOPBITS_ONE, serial.EIGHTBITS, 1, "serial_to_CAN")
    #ser_SAT = open_serial(SAT_port, SAT_baudrate, serial.PARITY_NONE, serial.STOPBITS_ONE, serial.EIGHTBITS, 1, "serial_to_SATEL")
    ser_SAT=0
    return(ser_CAN, ser_SAT)

def Main(ser_CAN, ser_SAT):
        a=1
        ser_CAN.write(sat_read_command)


if __name__ == '__main__':
    #inicjalizacja
    ser = serial.Serial('COM6',9600)
    ser.close()
    ser.open()
    ser.write(b"test")
    ser.close()
    ser_CAN, ser_SAT = Initialization()
    #petla glowna
    while True:
        Main(ser_CAN, ser_SAT)