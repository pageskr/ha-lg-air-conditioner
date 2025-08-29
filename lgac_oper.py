#!/usr/bin/python
# LG Airconditioner
# ew11 IP와 PORT 변경

import socket
import sys
import struct
import binascii

ip = '192.168.0.15';
port = 8899;
packet = '8000A3' + sys.argv[1]

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
except socket.error:
    print('Failed to create socket')
    sys.exit()

#print('Socket Created')

try:
    s.connect((ip, port))
except socket.error:
    print('Failed to connect to ' + ip + ':' + str(port))
    sys.exit()

#print('Socket Connected to ' + ip + ':' + str(port))

try:
    s.send(bytes.fromhex(packet))
except socket.error:
    print('Send failed')
    sys.exit()

#print('Message send successfully')

reply = s.recv(1024)
reply = binascii.hexlify(reply).decode()
print(reply)
s.close()
