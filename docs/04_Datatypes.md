# Datatypes

Datatypes are one of the properties of Datapoints. They define how the datapoint is displayed in Home Assistant.

## Common parameters

All DataTypes can take the following parameters:

| Parameter   | Type       | Default  | Description              |
|-------------|------------|----------|--------------------------|
| deviceClass | str        | None     | Device Class             |
| category    | str        | None     | Category (CONFIG etc)    |
| icon        | str        | None     | "mdi:thermometer" etc    |

## ModbusSensorData

This creates a "Sensor" entity. Typically used for most readonly values.

Parameters:  
| Parameter   | Type       | Default  | Description                |
|-------------|------------|----------|----------------------------|
| stateClass  | str        | None     | Sensor State Class         |
| units       | str        | None     | Units                      |
| enum        | Dict       | None     | {0: "Value0", 1: "Value1"} |

```
Datapoints[MY_GROUP] = {  
	"DatapointName": ModbusDatapoint(Address=0, DataType=ModbusSensorData(deviceClass=SensorDeviceClass.TEMPERATURE, units=UnitOfTemperature.CELSIUS)),  
}
```

## ModbusNumberData

This creates a "Number" entity. Typically used for numeric input.

Parameters: 
| Parameter | Type       | Default  | Description              |
|-----------|------------|----------|--------------------------|
| units     | str        | None     | Units                    |
| min_value | int        | 0        | Minimum value            |
| max_value | int        | 65535    | Maximum value            |
| step      | int        | 1        | Step (increment in UI)   |

```
Datapoints[MY_GROUP] = {  
	"DatapointName": ModbusDatapoint(Address=0, DataType=ModbusNumberData(deviceClass=NumberDeviceClass.TEMPERATURE, units=UnitOfTemperature, min_value=10, max_value=30, step=2)),  
}
```

## ModbusSelectData

This creates a "Select" entity. This creates a dropdown/select for enumerated values.

Parameters:  
| Parameter | Type       | Default  | Description                |
|-----------|------------|----------|----------------------------|
| options   | Dict       | None     | {0: "Value0", 1: "Value1"} |

```
Datapoints[MY_GROUP] = {
	"DatapointName": ModbusDatapoint(Address=0, DataType=ModbusSelectData(options={0: "Stopped", 1: "Running", 2: "Error"})),
}
```

## ModbusBinarySensorData

This creates a "BinarySensor" entity. Typically used to display binary values.
Use device class to get more specific texts in the UI.

This type has no specific parameters.

```
Datapoints[MY_GROUP] = {
	"DatapointName": ModbusDatapoint(Address=0, DataType=ModbusBinarySensorData(deviceClass=BinarySensorDeviceClass.OCCUPANCY)),
}
```

## ModbusSwitchData

This creates a "Switch" entity. Typically used for writable binary values.

This type has no specific parameters.

```
Datapoints[MY_GROUP] = {
	"DatapointName": ModbusDatapoint(Address=0, DataType=ModbusSwitchData()),
}
```

## ModbusButtonData

This creates a "Button" entity. A button press will set the corresponding tag.

This type has no specific parameters.

```
Datapoints[MY_GROUP] = {
	"DatapointName": ModbusDatapoint(Address=0, DataType=ModbusButtonData()),
}
```
