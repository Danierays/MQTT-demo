# MQTT Demo for IoT connectivity
## Device hierarchy

```txt
|-- gateway 0
|   |
|   |-- slave 0
|   |-- slave 1
|
|-- gateway 1
    |
    |-- slave 0
    |-- slave 1
```
### Design/Architecture
![image](https://user-images.githubusercontent.com/65251073/146211739-2736095b-b8fe-46de-8ffa-25f1f2bbd827.png)

## MQTT topic structure

- `gateways/:gwid/config` (retained)

    ```json
    {
        // The gateway identifier.
        "gwid": "gateway-0", 
        // This setting allows to filter log messages.
        "loglevel": "info",
        // Configure the fieldbus used by the gateway.
        "fieldbus": {
            // The fieldbus communication protocol. Currently only "modbus" is supported. 
            "protocol": "modbus",
            // Configure the modbus serial communication.
            "modbus": {
                // The modbus framing.
                "method": "rtu",
                // The serial port to be used for the modbus.
                "serial_port": "COM3",
                // The bit parity, can be either of none "N", even "E" or odd "O".
                "parity": "N",
                // The baudrate for the serial connection.
                "baudrate": 19200,
                // The size of a data word bits, can be only a multiple of 8.
                "bytesize": 8,
                // The number of stopbits. Usually, if parity is "N", the stopbit is 2, otherwise 1.
                "stopbits": 2,
                // The fieldbus communication timeout in seconds.
                "timeout": 10,
            }
        },
        // The configuration of the slaves connected to the gateway.
        "slaves": {
            "optima-0"
                // The name of the slave device. Must be unique for each gateway.
                "sid": "optima-0",
                // The slave address is a string to allow the usage of IP addresses in the future.
                "address": "0x14",
                // Configure the mapping between parameter names and registers.
                "registers": {
                    // Registers that can be read or written.
                    "holding": {
                        "room_temperature": {
                            // The address of the register.
                            "address": "0x1",
                            // The datatype as which the data should be read or written. Defaults to "int".
                            "datatype": "float",
                            // The unit of the parameter.
                            "unit": "°C",
                            // The offset, that is applied to the data value. Defaults to 0. 
                            "offset": -100,
                        },
                        "humidity_setpoint": {
                            "address": "0x6",
                            "datatype": "int",
                            "unit": "%",
                        },
                        "fan_speed": {
                            "address": "0x7",
                            "datatype": "int",
                            "unit": "rpm",
                        },
                        "fan_mode": {
                            "address": "0x33",
                            "datatype": "int",
                            "unit": "",
                        },
                    },
                    // Registers that can only be read.
                    "input": {
                        "supply_air": {
                            "address": "0x14",
                            "datatype": "int",
                            "unit": "m^3/h",
                            "offset": -300,
                        },
                        "fresh_air":{
                            "address": "0x15",
                            "datatype": "int",
                            "unit": "m^3/h",
                            "offset": -300,
                        },
                        "discharge_air":{
                            "address": "0x16",
                            "datatype": "int",
                            "unit": "m^3/h",
                            "offset": -300,
                        },
                        "extract_air":{
                            "address": "0x17",
                            "datatype": "int",
                            "unit": "m^3/h",
                            "offset": -300,
                        },
                        "humidity":{
                            "address": "0x20",
                            "datatype": "int",
                            "unit": "%",
                        }
                    }
                }
            }
        }
    }
    ```

- `gateways/:gwid/logs`

    ```json
    {
        // The loglevel of the message. Can be one of: "debug", "info", "warn", "error".
        "level": "info",
        // The context, where this message originates from.
        "category": "config",
        // The log message.
        "message": "Received gateway configuration.",
    }
    ```

- `gateways/:gwid/slaves/:sid/request`

    ```json
    {
        // Message ID to implement deduplication between different MQTT clients.
        "mid": "448d4761-1f33-4b9a-8301-926f2af5034d",
        // Type of the modbus request can be either "read" or "write" depending on the type of register accessed.
        "type": "write",
        // The register address to be accessed.
        "register": "fan_mode",
        // Data to be written to the named register. This is ignored if the type is "read".
        "data": 0,
    }
    ```

- `gateways/:gwid/slaves/:sid/response`

    ```json
    {
        // Message ID to implement deduplication between different MQTT clients.
        "mid": "448d4761-1f33-4b9a-8301-926f2af5034f",
        // Type of the modbus request can be either "read" or "write" depending on the type of register accessed.
        "type": "write",
        // The register address to be accessed can be either a named register from the slave configuration or a hex address.
        "register": "fan_mode",
        // Data in the register.
        "data": 0,
        // Error occurred if the string has at least one character.
        "error": "illegal address",
    }
    ```
