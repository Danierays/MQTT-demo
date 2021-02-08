"""
Python Implementation of Modbus TCP-communication + MQTT

---------------------------------------------------------
Data can be read/written from/to a remote MQTT client into the Optima module

REGISTER CONFIG provides the registers to be used while writing and reading data
reg_config is a topic on the mqtt server and is updated everytime register configurations are changed

SLAVE CONFIGS assigns optima device a slave ID. In this way, many slave devices can be hooked unto one client.
slave_config is a topic on the mqtt server and is updated everytime a slave device is added.

"""

#------------------------------------------------------------------------------------------------#
# Import the required libraries
#------------------------------------------------------------------------------------------------#
import serial
import socket
import traceback
import logging
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Defaults
from pymodbus.utilities import hexlify_packets
from pymodbus.factory import ServerDecoder
from pymodbus.datastore import ModbusServerContext
from pymodbus.device import ModbusControlBlock
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.transaction import *
from pymodbus.exceptions import NotImplementedException, NoSuchSlaveException
from pymodbus.pdu import ModbusExceptions as merror
from pymodbus.compat import socketserver, byte2int
from binascii import b2a_hex
from pymodbus.server.sync import StartTcpServer
from pymodbus.server.sync import ModbusTcpServer 
from pymodbus.server.sync import StartUdpServer
from pymodbus.server.sync import StartSerialServer
import pymodbus.server.sync
from pymodbus.server.sync import ModbusConnectedRequestHandler
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusBinaryFramer
from pymodbus.client.sync import ModbusTcpClient as ModbusClient

#------------------------------------------------------------------------------------------------------------------#
# Import mqtt client
#------------------------------------------------------------------------------------------------------------------#

import paho.mqtt.client as mqtt  
import json                     #used to convert reg_config and slave_config from received json format
import time

#-------------------------------------------------------------------------------------------------------------------#
# Defining global variables to store updates (registers, slave_ID) and device info
#-------------------------------------------------------------------------------------------------------------------#
holding_write_reg = {}
holding_read_reg = {}
input_reg = {}
#reg_config = {"Room Temperature":'12',"Humidity control":'22'}
slave_config = {}
#slave_id = {"HVAC_Unit":'0x14'}
device = ''

functional_code = 0     
read_reg = 0
write_reg = 0
value = 0

def on_connect(client, userdata, flags, rc):
    print("Connected to broker")
    
def on_disconnect(client, userdata,flags,rc=0):
    print("Disconnected with result code"+str(rc))
#--------------------------------------------------------------------------------------------------------------------#
# Device_in_use has the name of key(name) of the device being currently accessed.
#This function updates the device_in_use variable when a new device is accessed.
#--------------------------------------------------------------------------------------------------------------------#
def device_on_message(client, userdata, message):
    global device
    device = message.payload
    print("Device in use", device)

#--------------------------------------------------------------------------------------------------------------------#
#This function is called when data a data_write is made to the Optima.  It proceeds as follows:
#>First finds the device name from device global variable which as updated in device_on_message() function.
#>Then uses reg_config and slave_config corrresponding register number and slave_ID
#>Finally, it writes the data received into that register and slave ID of the Optima module by establishing a connection with the Modbus server
#--------------------------------------------------------------------------------------------------------------------#
def data_on_message(client, userdata, msg):
    global device
    global functional_code
    global write_reg
    dev = device.decode("utf-8")  #to convert from binary array to string
    
    data = json.loads(msg.payload)
    if data is None:
        return
    
    reg_type = data.get("reg_type")
    reg_type =str(reg_type)
    if reg_type == 'holding_reg':
        functional_code = 4
    
    telemetry_id = data.get("telemetry_id")
    telemetry_id = str(telemetry_id)
    write_reg = int(holding_write_reg[locals()['telemetry_id']])
    print("Register to write into :\n")
    print(write_reg)
    
    val = data.get("value")
    val=int(val)                  #value = int(message.payload)
    print("Value:", val)
    
    UNIT = int(slave_config[locals()['dev']])
    print("Slave unit to write into :\n")
    print(UNIT)
    
    mclient = ModbusClient(host = "localhost", port = 502,framer = ModbusRtuFramer) #Initialise the ModbusTcpClient
    mclient.connect()
    if functional_code == 3:
        print("Cannot write to an input register")
    elif functional_code == 4:
        rw = mclient.write_register(write_reg,value=val,unit=UNIT)

#--------------------------------------------------------------------------------------------------------------------#
#This function is called when data a data read request is sent from the remote mqtt_client(broker). It proceeds as follows:
#>Firstly, it gets the register number and slave ID(and does so by sending the device name as payload of the request message)
#>Then it establishes a Modbus TCP connection with the Optima and reads the value of the target register. this value is then published to 
#>data_req topic to which the remote client is subscribed.
#--------------------------------------------------------------------------------------------------------------------#
#confirmation that collected data has been published
def data_req_on_publish(client, userdata, mid):  
    print("Data request published\n")

def req_response_on_connect(client, userdata, flags, rc):
    print("Connection established.")

def read_req_on_message(client,userdata,msg):
    global functional_code
    global read_reg
    global value
    print("Data read request received")
    global device
    dev = device.decode("utf-8")
    print("Reading data from ",dev)
    
    data = json.loads(msg.payload)
    reg_type = data.get("reg_type")
    reg_type =str(reg_type)
    if reg_type == 'holding_reg':
        functional_code = 4
        print("Funtional code is: ",functional_code)
    elif reg_type =='input_reg':
        functional_code = 3
        print("Funtional code is: ",functional_code)
    
    telemetry_id = data.get("telemetry_id")
    telemetry_id = str(telemetry_id)
    if reg_type =='holding_reg':
        read_reg = int(holding_read_reg[locals()['telemetry_id']])
    elif reg_type == 'input_reg':
        read_reg = int(input_reg[locals()['telemetry_id']])
    
    print("Reg_value :",read_reg)
    UNIT = int(slave_config[locals()['dev']])
    mclient = ModbusClient(host = "localhost", port = 502, framer = ModbusRtuFramer) #Initialise the ModbusTcpClient
    mclient.connect()
    
    if functional_code == 4:
        rr = mclient.read_holding_registers(read_reg,1,unit=UNIT)
        if rr.isError():
            print('Modbus Error:', rr)
        else:
            value = rr.registers[0]
        client.publish('data_req',value,qos=2)
    
    elif functional_code == 3:
        rr = mclient.read_input_register(read_reg,1,unit=UNIT)
        if rr.isError():
            print('Modbus Error:', rr)
        else:
            value = rr.registers[0]
        client.publish('data_req',value,qos=2) #published to data_req to which user client is subscribed.
    print(value)
#--------------------------------------------------------------------------------------------------------------------#
#This function updates the reg_config and slave_config global variable when the respective variables are updated by the remote mtt client
# so that the data_on_message and read_req_on_message get values from the correct registers and slave unit(s) respectively.
#--------------------------------------------------------------------------------------------------------------------#

def reg_config_on_message(client, userdata, message):
    print("reg_config received\n")
    global holding_read_reg
    global holding_write_reg
    global input_reg                     #referring to global variable reg_config. 
    data = json.loads(message.payload)   #converting from json data
    print(data)
    holding_read_reg = data.get('holding_read_reg')
    holding_write_reg = data.get('holding_write_reg')
    input_reg = data.get('input_reg')
    

def slave_config_on_message(client,userdata,message):
    print("slave_config received")
    global slave_config                           #referring to global variable slave_config. 
    slave_config = json.loads(message.payload)    #converting from json data
    print(slave_config)

#--------------------------------------------------------------------------- #
# configure the service logging
# --------------------------------------------------------------------------- #
FORMAT = ('%(asctime)-15s %(threadName)-15s'
          ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.DEBUG)

#--------------------------------------------------------------------------- #
#Using online mqtt broker
# --------------------------------------------------------------------------- #
broker_address = "test.mosquitto.org"

#---------------------------------------------------------------------------------------------------------------------------------#
#creating a reg_config instance. this instance subscribes to, and hence receives data from the topic; reg_config
#Therefore any changed made in reg_config by client and uploaded to this topic will be received at this remote mqtt client as well
#Once received, reg_config global is updated
#---------------------------------------------------------------------------------------------------------------------------------#
print("creating reg_config instance")
client_reg = mqtt.Client("REG")
client_reg.on_message = reg_config_on_message
print("connecting to broker")
client_reg.connect(broker_address,1883)
client_reg.loop_start()
print("Subscribing to reg_config")
client_reg.subscribe('reg_config',qos=2)

#------------------------------------------------------------------------------------------------------------#
# Creating a slave_config instance. This instance subscribes to and hence receives data from the topic; slave_config.
# Therefore, any changes made in slave_config by client and uploaded to this topic is received by this client.
# Once received, slave_config global variable is updated.
#------------------------------------------------------------------------------------------------------------#
print("creating slave_config instance")
client_slave = mqtt.Client("SLAVE")
client_slave.on_message = slave_config_on_message
print("connecting to broker")
client_slave.connect(broker_address,1883)
client_slave.loop_start()
print("Subscribing to slave_config")
client_slave.subscribe('slave_config',qos=2)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# Creating device_in_use instance. This instance subscribes to and hence receives data from topic device_in_use.
# Whenever a request is send by the user to read/write from the Optima module, the name of the slave which has been requested is updated(fetched) on this topic and received by this client.
# Once received, device_in_use global variable is updated.
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
print("Creating device_in_use instance")
client_dev = mqtt.Client("DIU")
client_dev.on_message = device_on_message
print("connecting to broker")
client_dev.connect(broker_address,1883)
client_dev.loop_start()
print("Subscribing to device_in_use")
client_dev.subscribe('device_in_use',qos=2)

#----------------------------------------------------------------------------------------------------------------------------------------------#
# Creating data write instance. This instance subscribes and hence receives data from topic; data.
# Whenever data to write into a slave is sent by the client, it is updated on this topic and received by this client.
# Once received, it is written into the register specified by reg_config of that slave and slave unit specified by slave_config in function data_on_message.
#----------------------------------------------------------------------------------------------------------------------------------------------#
print("Creating data instance")
client_data = mqtt.Client("DATA")
client_data.on_message = data_on_message
print("connecting to broker")
client_data.connect(broker_address,1883)
client_data.loop_start()
print("Subscribing to data")
client_data.subscribe('data',qos=2)

#-----------------------------------------------------------------------------------------------------------------------------------------------------#
# Creating data request instance. This instance subscribes and hence receives data from topic; read_req.
# Whether data is to be read from a slave, the name of the slave to read data from is updated on this topic and hence received by this client.
# Once received, it is read from register specified by reg_config of that slave and published to be received by user in method read_req_on_message.
#-----------------------------------------------------------------------------------------------------------------------------------------------------#
print("Creating data req instance")
client_data_req = mqtt.Client("DATA_REQ")
client_data_req.on_message = read_req_on_message
client_data_req.on_publish = data_req_on_publish
print("connecting to broker")
client_data_req.connect(broker_address,1883)
client_data_req.loop_start()
print("Subscribing to read req")
client_data_req.subscribe('read_req',qos=2)

#-------------------------------------------------------------------------------------------------------#
#time delay to keep this client online, running and waiting for requests. Can be manually shut down.
#-------------------------------------------------------------------------------------------------------#
time.sleep(100000) 

#-----------------------------------------------------------------------------------------------------#
#stop loops and disconnect all clients
#-----------------------------------------------------------------------------------------------------#
client_reg.loop_stop()
client_slave.loop_stop()
client_dev.loop_stop()
client_data.loop_stop()
client_data_req.loop_stop()
client_reg.disconnect()
client_slave.disconnect()
client_dev.disconnect()
client_data.disconnect()
client_data_req.disconnect()
