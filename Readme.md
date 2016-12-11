Modbus TCP to Modbus RTU gateway

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](http://creativecommons.org/licenses/by-nc/4.0/)  

This is my Modbus TCP to Modbus RTU gateway written in Python.
I run it on a [BeagleBone Green](http://beagleboard.org/Green) equiped with a [Waveshare CAN RS485 Cape](www.waveshare.com/wiki/RS485_CAN_CAPE) to communicate with my centralized ventilation system.

I've only tested Modbus functions [01,02,03,04,06] so far because I don't need any other functions for my purpose.
Maybe the gateway need to be exteded to support other functions.

The gateway receives a ModbusTCP frame, translates it into a ModbusRTU frame, takes the ModbusRTU response and converts that into the ModbusTCP response for the initial request.

How to use:
```
git clone https://github.com/Bouni/ModBusGateway.git
cd ModBusGateway
python modbus-gateway.py
```

The configuration can be changed by editing the modbus-gateway.cfg file.

A more detailed description can be found here:
- http://blog.bouni.de/blog/2016/12/02/rs485-on-a-beaglebonegreen-plus-waveshare-cape/
- http://blog.bouni.de/blog/2016/12/10/modbus-tcp-to-modbus-rtu-gatway-on-a-beaglebone-green/
