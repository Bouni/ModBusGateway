#/usr/bin/env python

import fcntl
import struct
import socket
import serial
import logging
import crc16

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d: %(levelname)s - %(message)s')
logger = logging.getLogger('Modbus Gateway')

class ModbusGateway:

    def __init__(self, host='', tcpport=502, serial_port='/dev/ttyO4', baud=19200):
        self.host = host
        self.tcpport = tcpport
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, tcpport))
        self.socket.listen(1)
        self.serial = serial.Serial()
        self.port = serial_port
        self.baud = baud
        self.serial_config()
        self.run()

    def serial_config(self):
        self.serial.port = self.port
        self.serial.baudrate = self.baud
        self.serial.stopbits = 1
        self.serial.parity = 'E'
        self.serial.bytesize = 8
        self.serial.timeout = 5
        self.serial.open()
        RS485_CONFIG = struct.pack('IIIIIIII',0x21,0,0,7,0,0,0,0)
        fcntl.ioctl(self.serial.fileno(), 0x542F, RS485_CONFIG)

    def serial_connect(self):
        self.serial.open()
        logger.debug("Serial Connection: {}".format(self.serial))

    def tcp_start(self):
        logger.info("Waiting for incoming TCP connection")
        self.connection, self.client = self.socket.accept()
        logger.debug('TCP Connection from {}, port {}'.format(self.client[0], self.client[1]))

    def rtu_request(self, request):
        logger.debug("RTU Request {}".format(":".join("{:02X}".format(ord(c)) for c in request)))
        self.serial.write(request)
        response = self.serial.read(3)
        if ord(response[0]) > 0x80:
            return response
        response += self.serial.read(ord(response[2]) + 2)
        logger.debug("RTU Response {}".format(":".join("{:02X}".format(ord(c)) for c in response)))
        self.serial.flushInput()
        return response
            


    def run(self):
        while True:
            if not self.serial.isOpen():
                self.serial_connect()
            self.tcp_start()
            while True:
                logger.info("Waiting for incoming TCP message")
                data = self.connection.recv(12)
                if not data:
                    break
                logger.debug("TCP Request {}".format(":".join("{:02X}".format(ord(c)) for c in data)))
                rtu_msg = data[6:] + crc16.calculate(data[6:])
                rtu_response = self.rtu_request(rtu_msg)
                tcp_response = data[0:5] + chr(ord(rtu_response[2]) + 2) + rtu_response[0:-2]
                logger.debug("TCP Response {}".format(":".join("{:02X}".format(ord(c)) for c in tcp_response)))
                self.connection.send(tcp_response)

if __name__ == "__main__":
    mg = ModbusGateway()
