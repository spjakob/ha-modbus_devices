# EntityData

EntityData is one of the properties of Datapoints. They define how the datapoint is displayed in Home Assistant.

## Common parameters

All EntityDatas can take the following parameters:

| Parameter   | Type       | Default  | Description              |
|-------------|------------|----------|--------------------------|
| attrs       | dict       | None     | Dict for attributes      |
| deviceClass | str        | None     | Device Class             |
| category    | str        | None     | Category (CONFIG etc)    |
| icon        | str        | None     | "mdi:thermometer" etc    |

## EntityDataSensor

This creates a "Sensor" entity. Typically used for most readonly values.

Parameters:  
| Parameter   | Type       | Default  | Description                |
|-------------|------------|----------|----------------------------|
| stateClass  | str        | None     | Sensor State Class         |
| units       | str        | None     | Units                      |
| enum        | dict       | None     | {0: "Value0", 1: "Value1"} |

```
Datapoints[MY_GROUP] = {  
	"DatapointName": ModbusDatapoint(address=0, entity_data=EntityDataSensor(deviceClass=SensorDeviceClass.TEMPERATURE, units=UnitOfTemperature.CELSIUS)),  
}
```

## EntityDataNumber

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
	"DatapointName": ModbusDatapoint(address=0, entity_data=EntityDataNumber(deviceClass=NumberDeviceClass.TEMPERATURE, units=UnitOfTemperature, min_value=10, max_value=30, step=2)),  
}
```

## EntityDataSelect

This creates a "Select" entity. This creates a dropdown/select for enumerated values.

Parameters:  
| Parameter | Type       | Default  | Description                |
|-----------|------------|----------|----------------------------|
| options   | Dict       | None     | {0: "Value0", 1: "Value1"} |

```
Datapoints[MY_GROUP] = {
	"DatapointName": ModbusDatapoint(address=0, entity_data=EntityDataSelect(options={0: "Stopped", 1: "Running", 2: "Error"})),
}
```

## EntityDataBinarySensor

This creates a "BinarySensor" entity. Typically used to display binary values.
Use device class to get more specific texts in the UI.

This type has no specific parameters.

```
Datapoints[MY_GROUP] = {
	"DatapointName": ModbusDatapoint(address=0, entity_data=EntityDataBinarySensor(deviceClass=BinarySensorDeviceClass.OCCUPANCY)),
}
```

## EntityDataSwitch

This creates a "Switch" entity. Typically used for writable binary values.

This type has no specific parameters.

```
Datapoints[MY_GROUP] = {
	"DatapointName": ModbusDatapoint(address=0, entity_data=EntityDataSwitch()),
}
```

## EntityDataButton

This creates a "Button" entity. A button press will set the corresponding tag.

This type has no specific parameters.

```
Datapoints[MY_GROUP] = {
	"DatapointName": ModbusDatapoint(address=0, entity_data=EntityDataButton()),
}
```
