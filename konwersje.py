
import binascii

sat_read_command = b"FEFE00D7E2FE0D"



def transform_data(data):
    if(type(data) == type('String')):
        data = bytearray(data,'ascii')
    return data

a=b'BAM\1'
b=''.join("{:02x}".format(lit) for lit in a)
print("a: {}".format(a))
print("binascii.hexlify(a):\t{}".format(binascii.hexlify(a)))
print("wersja bez znacznikow \t{}".format(b))

c="string014a"
d=transform_data(c)
print("\na: {}\nb: {}\nc: {}\nd: {}".format(a,b,c,d))
print("binascii.hexlify(d):\t{}".format(binascii.hexlify(d)))
print("sat_read_command:  \t\t{}".format(sat_read_command))

