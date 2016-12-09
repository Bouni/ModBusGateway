#/usr/bin/env python

import fcntl
import struct
import ConfigParser
import SocketServer
import serial
import logging
import crc16

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s: %(levelname)-8s - %(message)s')
logger = logging.getLogger('Modbus Gateway')

class ModbusGateway(SocketServer.BaseRequestHandler):

    def setup(self):
        self.load_config()
        self.serial = serial.Serial()
        self.serial_config()

    def load_config(self):
        self.config = ConfigParser.RawConfigParser()
        self.config.read('modbus-gateway.cfg')

    def serial_config(self):
        self.serial.port = self.config.get("ModbusRTU", "port")
        self.serial.baudrate = self.config.getint("ModbusRTU", "baudrate")
        self.serial.stopbits = self.config.getint("ModbusRTU", "stopbits")
        self.serial.parity = self.config.get("ModbusRTU", "parity")
        self.serial.bytesize = self.config.getint("ModbusRTU", "bytesize")
        self.serial.timeout = self.config.getint("ModbusRTU", "timeout")
        self.serial_connect()
        RS485_CONFIG = struct.pack('IIIIIIII',
            0x21,0,0,
            self.config.getint("ModbusRTU", "gpio"),
            0,0,0,0)
        fcntl.ioctl(self.serial.fileno(), 0x542F, RS485_CONFIG)

    def serial_connect(self):
        if not self.serial.isOpen():
            self.serial.open()
            logger.debug("Serial Connection open")

    def handle(self):
        # check if serial port is open, open if not
        if not self.serial.isOpen():
            self.serial_connect()
        logger.info("Connection established with {}".format(self.client_address[0]))
        while True:
            # receive the ModbusTCP request
            tcp_request = self.request.recv(12)
            if not tcp_request or len(tcp_request) != 12:
                logger.info("Connection closed")
                break
            logger.debug("TCP Request {}".format(":".join("{:02X}".format(ord(c)) for c in tcp_request)))
            # convert ModbusTCP request into a ModbusRTU request
            rtu_request = tcp_request[6:] + crc16.calculate(tcp_request[6:])
            logger.debug("RTU Request {}".format(":".join("{:02X}".format(ord(c)) for c in rtu_request)))
            # make sure that the input buffer is clean
            self.serial.flushInput()
            # send the ModbusRTU request 
            self.serial.write(rtu_request) 
            # read first three bytes of the response to check for errors
            rtu_response = self.serial.read(3)
            if ord(rtu_response[1]) > 0x80:
                logger.debug("RTU Error Response {}".format(":".join("{:02X}".format(ord(c)) for c in rtu_response)))
                tcp_response = tcp_request[0:5] + chr(3) + rtu_response
                logger.debug("TCP Error Response {}".format(":".join("{:02X}".format(ord(c)) for c in tcp_response)))
                self.request.sendall(tcp_response)
            else:
                # if no error, read number of bytes indicated in RTU response
                rtu_response += self.serial.read(ord(rtu_response[2]) + 2)
                logger.debug("RTU Response {}".format(":".join("{:02X}".format(ord(c)) for c in rtu_response)))
                # convert ModbusRTU response into a Modbus TCP response 
                tcp_response = tcp_request[0:5] + chr(ord(rtu_response[2]) + 2) + rtu_response[0:-2]
                logger.debug("TCP Response {}".format(":".join("{:02X}".format(ord(c)) for c in tcp_response)))
                # return converted TCP response
                self.request.sendall(tcp_response)

    def finish(self):
        self.serial.close()

if __name__ == "__main__":
    config = ConfigParser.RawConfigParser()
    config.read('modbus-gateway.cfg')
    address = (config.get("ModbusTCP", "host"), config.getint("ModbusTCP","port"))
    server = SocketServer.TCPServer(address, ModbusGateway)
    server.serve_forever()
