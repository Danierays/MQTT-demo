"""
Pymodbus Asynchronous Client-Server 

-------------------------------------------------------
This Client does the following:
- Read/Write Data to the Holding Registers(4x) of the Optima module.
- Read Data from the Input registers(3x).
The modbus addresses used here are those documented by LS Control.

The Server is responsible for encapsulating Modbus RTU frames for communication over MQTT
"""

#----------------------------------------------------------------------------#
# Import the required Client libraries
#----------------------------------------------------------------------------#

import pymodbus
import time
import logging

#----------------------------------------------------------------------------#
# Choose the required modbus protocol (Serial CLient)
#----------------------------------------------------------------------------#

from pymodbus.client.sync import ModbusSerialClient as ModbusClient

# --------------------------------------------------------------------------- #
# Importing the required Server libraries
# --------------------------------------------------------------------------- #

from pymodbus.server.sync import StartTcpServer as StartServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore.remote import RemoteSlaveContext

#----------------------------------------------------------------------------#
# Configure the client logging...
#----------------------------------------------------------------------------#

FORMAT = ('%(asctime)-15s %(threadName)-15s'
          ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.DEBUG)

#----------------------------------------------------------------------------#
# Defining a few constants...
#----------------------------------------------------------------------------#

PORT = 'COM3'
BAUDRATE = 19200
UNIT = 0x14

#----------------------------------------------------------------------------#
# Implementing Client
#----------------------------------------------------------------------------#

client = ModbusClient(method='rtu', port=PORT, bytesize=8, stopbits=1, timeout=2, parity='E', baudrate=BAUDRATE)

#----------------------------------------------------------------------------#
# Data store
#----------------------------------------------------------------------------#

store = RemoteSlaveContext(client, unit=UNIT)

context = ModbusServerContext(slaves=store, single=True)
identity = ModbusDeviceIdentification()
identity.VendorName = 'KVM-Genvex A/S'
identity.ProductCode = '297986329025'
identity.VendorUrl = 'https://www.genvex.com/en'
identity.ProductName = 'OPT270'
identity.ModelName = 'TCP Server'
    
# ----------------------------------------------------------------------- #
# Running the server
# ----------------------------------------------------------------------- #
StartServer(context, identity=identity, address=("localhost", 502), framer = ModbusRtuFramer)
      


