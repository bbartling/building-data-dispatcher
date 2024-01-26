from bacpypes3.pdu import Address
from bacpypes3.primitivedata import ObjectIdentifier


DEVICE1_SCRAPE_INTERVAL = 60
DEVICE2_SCRAPE_INTERVAL = 120

# Define BACnet properties
BACNET_PRESENT_VALUE_PROP_IDENTIFIER = "present-value"
BACNET_PROPERTY_ARRAY_INDEX = None

# Define points
DUCT_TEMP = ObjectIdentifier("analog-input,2")
ZONE_SETPOINT = ObjectIdentifier("analog-value,302")
OUT_TEMP = ObjectIdentifier("analog-value,301")

# Define devices and their configurations
devices = {
    "device1": {
        "address": Address("12345:2"),
        "scrape_interval": 60,  # in seconds
        "points": [
            ("DUCT_TEMP", DUCT_TEMP),
            ("ZONE_SETPOINT", ZONE_SETPOINT),
            ("OUT_TEMP", OUT_TEMP)
        ]
    },
    "device2": {
        "address": Address("12345:6"),
        "scrape_interval": 120,  # in seconds
        "points": [
            ("DUCT_TEMP", DUCT_TEMP),
            ("ZONE_SETPOINT", ZONE_SETPOINT),
            ("OUT_TEMP", OUT_TEMP)
        ]
    },
    # Add more devices here
}
