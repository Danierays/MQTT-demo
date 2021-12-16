"""
@brief: Python Implementation of a remote MQTT client. 
@author: Daniel Isaac K. Njamen

@date: <02/03/2021>
-------------------------------------------------------------------------------------------
reg_configs as well as the slave_configs are defines here. Meaning that the remote user sends read/write
requests to the MQTT broker with information such as the device_ID and the target register(s).
The remote MQTT client is connected to iot.sclipse.org MQTT server.
"""

import paho.mqtt.client as mqtt
import time
import json

#--------------------------------------------------------------------------------------------------#
#reg_config dictionary
#reg_config = {"telemetry_id":reg_value}
#A nested register can be used to store these registers and their names used as keys.
#--------------------------------------------------------------------------------------------------#
holding_write_reg = {"Room_Temp":'1', "Humidity_Cntrl":'22', "Fan_Spd_level":'24', "Fan_mode":'112'}
holding_read_reg  = {"Room_Temp":'1', "Humidity_Control":'06', "Fan_Speed_level":'07', "Fan_mode":'51'}

input_reg = {'Supply_air':'20', 'Fresh_air':'21','Discharge_air':'22','Extract_air':'23', 'Humidity_Sensor':'26'}
#--------------------------------------------------------------------------------------------------#
#slave_config dictionary
#slave_id = {"Device":slave_id}
#--------------------------------------------------------------------------------------------------#
slave_config ={'OPT270':0x14}
 
read_req_value = 0  #to store response of read_req. 

#method to display a message once the user(client1) has connected to MQTT server. Called when connection is successful.
def on_connect(client, userdata, flags, rc):
     #print("Connected flags"+str(flags)+"result code "\
     #+str(rc)+"client1_id")
     #client.connected_flag=True
    pass
#method to display a message when the data has been published by user client (client1). Called when publish is successful.
def on_publish(client, userdata, mid):
    print("Data published.")

#Callback function to print the data received from the register after sending a read request.(The callback for when a PUBLISH message is received from the server)
def data_req_on_message(client,userdata,message):
    global read_req_value
    print("Data received :\n")
    read_req_value = message.payload     #data.get('value') In case that the data is not retrievable
    print("Register value :\n")
    print(read_req_value)
    
broker_address="test.mosquitto.org" #Using online broker

#-------------------------------------------------------------------------------------------------------------------------------------------------------#
# Creating instance client1. This client is the end user which will send requests to read/write data from modbus tcp slaves and can be a remote client. 
# The requests from client1 are sent to the MQTT server. Client2 receives the requests, reg and slave config from the respective topics on MQTT server. 
# Client2 is both an MQTT client and MODBUS client. It sends the received request to the MODBUS server to create/write data from the slaves. 
#--------------------------------------------------------------------------------------------------------------------------------------------------------#
print("creating new instance")
client1 = mqtt.Client("P1", clean_session= True)
client1.on_connect = on_connect
client1.on_publish = on_publish
client1.on_message = data_req_on_message
print("connecting to broker")
client1.connect(broker_address,1883) #connect to encrypted MQTT broker
client1.loop_start()            #start the loop

print("Pushing reg_configs")
client1.publish('reg_config',json.dumps({'holding_write_reg':holding_write_reg,'holding_read_reg':holding_read_reg,'input_reg':input_reg}),qos=2) #Pushing initial reg_config
time.sleep(2)                                              #delay to wait till reg_config is pushed before prompting for data input

print("Pushing slave_config")
client1.publish('slave_config',json.dumps(slave_config),qos=2)  #Pushing initial slave_config
time.sleep(2)                                                   #delay to wait till slave_config is pushed before prompting for data input

print("Subscribing to data request")
client1.subscribe('data_req',qos=2)  #Subscribing to data request topic where the requested data from register is published by client2. 
time.sleep(2)

#--------------------------------------------------------------------------------------------#
#Control loop
#--------------------------------------------------------------------------------------------#
cont = 'Y' #loop control variable
while cont == 'Y':
    choice = input('1)data_write\n2)data_read\n3)reg_config\n4)slave_config\n')
    
    if choice == '3':
        print(holding_write_reg)
        print(holding_read_reg)
        print(input_reg)
        choice = input('1)Add new\n2)Exit\n')
        if choice == '1':
            #reg_type = str(input("Enter reg_type(Options: holding_reg|input_reg)\n"))
            telemetry_id = input('Enter telemetry_id(fx:Room_temperature)\n')
            value = int(input('Enter new register number\n'))
            reg_config[locals()['telemetry_id']] = value #Updating reg_config dict. key is given using locals() function which returns all local variables. locals()['telemetry_id'] will return the string which is stored in variable name 'device'
        elif choice ==  '2':
            continue
        else:
            print("Invalid choice\n")
            continue
        print("new reg_config:\n")
        print(reg_config)
        print("Pushing reg_config\n")
        client1.publish('reg_config',json.dumps({'holding_write_reg':holding_write_reg,'holding_read_reg':holding_read_reg,'input_reg':input_reg}),qos=2)
        time.sleep(3)
   
   
    elif choice == '4':
        print(slave_config)
        choice = input('1)Choose device\n2)Modify existing\n3)Exit\n')
        if choice== '1':
            device = input('Select device\n')
            try:
                UNIT = int(slave_config[locals()['device']])
                print("Slave_id", UNIT)
            except:
                print("Device does not exist in database. Please add the device to slave_config or select existing device.")
            continue 
        
        if choice == '2':
            device = input('Enter device\n')
            new_value = input('Enter new slave ID\n')
            slave_config[locals()['device']] = new_value #Updating slave_config dict. key is given using locals() function which returns all local variables. locals()['device'] will return the string which is stored in variable name 'device'
        
        elif choice == '3':
            continue
        else:
            print("Invalid choice\n")
            continue
        print("new slave_config:\n")
        print(slave_config)
        print("Pushing slave_config\n")
        client1.publish('slave_config',json.dumps(slave_config),qos=2)
        time.sleep(2)
      
      
    elif choice == '1':
        device = input('Select device to which you want to write data to:\n')
        try:
            UNIT = int(slave_config[locals()['device']])  #Checking if entered device has been added as a slave.
        except:
            print("Device does not exist in database. Please add the device to slave_config or select existing device.")
            continue 
        reg_type = input('Enter reg_type(Options: holding_reg|input_reg)\n')
        if reg_type == 'holding_reg':
            reg_type = 'holding_reg'
        elif reg_type == 'input_reg':
            print("Cannot write to an input register.")
            break
        print("Choose the telemetry to be written to :\n",holding_write_reg)
        telemetry_id = input('Enter telemetry_id to write to:\n')
        value = int(input('Enter value(in decimal) to put in register :\n'))
        #count = int(input("Enter number of registers to be read starting from the base register(fetched by program using the telemetry_id key) :\n"))
        
        print("Writing to register\n",value)
        print("Publishing value to device\n",device)
        
        client1.publish('device_in_use',device,qos = 2) #publish the device currently in use. the register number of that device is taken from reg_config and value is written.
        client1.publish('data', payload=json.dumps({'reg_type':reg_type, 'telemetry_id':telemetry_id ,'value':value}),qos = 2) #publish value to be put in register
        time.sleep(2)
    
    elif choice == '2':
        device = input("Select device from which data is to be read:\n")
        try:
            UNIT = int(slave_config[locals()['device']])  #Checking if entered device has been added as a slave.
        except:
            print("Device does not exist in database. Please add device to slave_config or select existing device.")
            continue
        reg_type = input("Enter reg_type(Options: holding_reg|input_reg)\n")
        if reg_type == 'holding_reg':
            print("Choose telemetry id to read from", holding_read_reg)
        elif reg_type == 'input_reg':
            print("Choose telemetry_id to read from", input_reg)
        telemetry_id = input("Enter telemetry_id to read:\n")
        
        client1.publish('device_in_use',device,qos = 2)
        client1.publish('read_req',payload=json.dumps({'reg_type':reg_type,'telemetry_id':telemetry_id}),qos=2)
        time.sleep(5)
    else:
        print("Invalid choice")
    cont = input("Continue? [Y/N]\n")
time.sleep(4)
client1.loop_stop()
