
from bacpypes3.pdu import Address
from bacpypes3.primitivedata import ObjectIdentifier


DUCT_TEMP = ObjectIdentifier("analog-input,2")
ZONE_SETPOINT = ObjectIdentifier("analog-value,302")
OUT_TEMP = ObjectIdentifier("analog-value,301")

DEVICE1_ADDRESS = Address("12345:2")
DEVICE2_ADDRESS = Address("12345:6")

DEVICE1_SCRAPE_INTERVAL = 60
DEVICE2_SCRAPE_INTERVAL = 120

BACNET_PRESENT_VALUE_PROP_IDENTIFIER = "present-value"
BACNET_PROPERTY_ARRAY_INDEX = None

READ_REQUESTS = [
    (
        DEVICE1_ADDRESS,
        DUCT_TEMP,
        BACNET_PRESENT_VALUE_PROP_IDENTIFIER,
        BACNET_PROPERTY_ARRAY_INDEX,
        "device1_duct_temp",
        
    ),
    (
        DEVICE1_ADDRESS,
        ZONE_SETPOINT,
        BACNET_PRESENT_VALUE_PROP_IDENTIFIER,
        BACNET_PROPERTY_ARRAY_INDEX,
        "device1_zone_setpoint",
    ),
    (
        DEVICE1_ADDRESS,
        OUT_TEMP,
        BACNET_PRESENT_VALUE_PROP_IDENTIFIER,
        BACNET_PROPERTY_ARRAY_INDEX,
        "device1_out_temp",

    ),
    (
        DEVICE2_ADDRESS,
        DUCT_TEMP,
        BACNET_PRESENT_VALUE_PROP_IDENTIFIER,
        BACNET_PROPERTY_ARRAY_INDEX,
        "device2_duct_temp",
    ),
    (
        DEVICE2_ADDRESS,
        ZONE_SETPOINT,
        BACNET_PRESENT_VALUE_PROP_IDENTIFIER,
        BACNET_PROPERTY_ARRAY_INDEX,
        "device2_zone_setpoint",
    ),
    (
        DEVICE2_ADDRESS,
        OUT_TEMP,
        BACNET_PRESENT_VALUE_PROP_IDENTIFIER,
        BACNET_PROPERTY_ARRAY_INDEX,
        "device2_out_temp",
    ),
]
