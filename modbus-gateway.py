#/usr/bin/env python

import fcntl
import struct
import SocketServer
import serial
import logging
import crc16

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d: %(levelname)s - %(message)s')
logger = logging.getLogger('Modbus Gateway')
logger.setFormatter(logging.Formatter("%(asctime)s.%(msecs)03d - %(levelname)s : %(message)s","%Y.%m.%d %H:%M:%S"))

class ModbusGateway(SocketServer.BaseRequestHandler):

    def __init__(self, port='/dev/ttyO4', baud=19200):
        self.serial = serial.Serial()
        self.port = serial_port
        self.baud = baud
        self.serial_config()

    def serial_config(self):
        self.serial.port = self.port
        self.serial.baudrate = self.baud
        self.serial.stopbits = 1
        self.serial.parity = 'E'
        self.serial.bytesize = 8
        self.serial.timeout = 5
        self.serial_connect()
        RS485_CONFIG = struct.pack('IIIIIIII',0x21,0,0,7,0,0,0,0)
        fcntl.ioctl(self.serial.fileno(), 0x542F, RS485_CONFIG)

    def serial_connect(self):
        if not self.serial.isOpen():
            self.serial.open()
            logger.debug("Serial Connection: {}".format(self.serial))

    def handle(self):
        # check if serial port is open, open if not
        if not self.serial.isOpen():
            self.serial_connect()
        logger.info("Waiting for incoming TCP message")
        # receive the ModbusTCP request
        tcp_request = self.request.recv(12)
        logger.debug("TCP Request {}".format(":".join("{:02X}".format(ord(c)) for c in tcp_request)))
        # convert ModbusTCP request into a ModbusRTU request
        rtu_request = tcp_request[6:] + crc16.calculate(tcp_request[6:])
        logger.debug("RTU Request {}".format(":".join("{:02X}".format(ord(c)) for c in rtu_request)))
        # make sure that the input buffer is clean
        self.serial.flush()
        # send the ModbusRTU request 
        self.serial.write(rtu_request) 
        # read first three bytes of the response to check for errors
        rtu_response = self.serial.read(3)
        if ord(rtu_response[1]) > 0x80:
            logger.debug("Modbus Error {}".format(":".join("{:02X}".format(ord(c)) for c in rtu_response)))
            tcp_response = tcp_request[0:5] + chr(3) + rtu_response
            logger.debug("TCP Error Response {}".format(":".join("{:02X}".format(ord(c)) for c in tcp_response)))
            self.request.sendall(tcp_response())
            return
        # if no error, read number of bytes indicated in RTU response
        rtu_response += self.serial.read(ord(rtu_response[2]) + 2)
        logger.debug("RTU Response {}".format(":".join("{:02X}".format(ord(c)) for c in rtu_response)))
        # convert ModbusRTU response into a Modbus TCP response 
        tcp_response = tcp_request[0:5] + chr(ord(self.rtu_response[2]) + 2) + rtu_response[0:-2]
        logger.debug("TCP Response {}".format(":".join("{:02X}".format(ord(c)) for c in tcp_response)))
        # return converted TCP response
        self.request.sendall(tcp_response())


if __name__ == "__main__":
    server = SocketServer.TCPServer(('', 502), ModbusGateway)
    server.serve_forever()
