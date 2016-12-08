#/usr/bin/env python

import fcntl
import struct
import SocketServer
import serial
import logging
import crc16

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d: %(levelname)s - %(message)s')
logger = logging.getLogger('Modbus Gateway')

class ModbusFrame:
    
    def __init__(self, data):
        self._tcp_request = data
        self._rtu_request = None
        self._rtu_response = None
        self._tcp_response = None
        logger.debug("TCP Request {}".format(":".join("{:02X}".format(ord(c)) for c in self._tcp_request)))

    def rtu_request(self):
        self._rtu_request = self._tcp_request[6:] + crc16.calculate(self._tcp_request[6:])
        logger.debug("RTU Request {}".format(":".join("{:02X}".format(ord(c)) for c in self._rtu_request)))
        return _rtu_request 

    def rtu_response(self, data):
        self._rtu_response = data
        logger.debug("RTU Response {}".format(":".join("{:02X}".format(ord(c)) for c in self._rtu_response)))

    def tcp_response(self):
        self._tcp_response = _tcp_request[0:5] + chr(ord(self._rtu_response[2]) + 2) + self._rtu_response[0:-2]
        logger.debug("TCP Response {}".format(":".join("{:02X}".format(ord(c)) for c in self._tcp_response)))
        return self._tcp_response


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
        # pass received tcp data to ModbusFrame
        modbus_frame = ModbusFrame(self.request.recv(12))
        # write ModbusFrame RTU conversion to serial port
        self.serial.write(modbus_frame.rtu_request())
        # read first three bytes of the response to check for errors
        rtu_response = self.serial.read(3)
        if ord(rtu_response[0]) > 0x80:
            logger.debug("Modbus Error {}".format(":".join("{:02X}".format(ord(c)) for c in rtu_response)))
            return
        # if no error, read number of bytes indicated in RTU response
        rtu_response += self.serial.read(ord(rtu_response[2]) + 2)
        # pass received RTU data to ModbusFrame
        modbus_frame.rtu_response(rtu_response)
        # return converted TCP response
        self.request.sendall(modbus_frame.tcp_response())


if __name__ == "__main__":
    server = SocketServer.TCPServer(('', 502), ModbusGateway)
    server.serve_forever()
