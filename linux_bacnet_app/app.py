from bacpypes3.argparse import SimpleArgumentParser
from bacpypes3.local.binary import BinaryValueObject
from bacpypes3.app import Application
from bacpypes3.apdu import ErrorRejectAbortNack
from bacpypes3.local.binary import BinaryValueObject
from bacpypes3.vendor import get_vendor_info
from bacpypes3.apdu import (
    ErrorRejectAbortNack,
    PropertyReference,
    PropertyIdentifier,
    ErrorType,
)

from bacpypes3.pdu import Address
from bacpypes3.primitivedata import ObjectIdentifier

import asyncio
import os
import asyncio
import logging
import aiofiles
from datetime import datetime
import psutil
from typing import Callable, List, Optional, Tuple
import yaml
import traceback

# examples args for bacpypes3. Run like:
# $ python3 app.py --name Slipstream --instance 3056672 --address 10.7.6.201/24:47820

# Define BACnet properties
BACNET_PRESENT_VALUE_PROP_IDENTIFIER = "present-value"
BACNET_PROPERTY_ARRAY_INDEX = None

logging.basicConfig(level=logging.DEBUG)

_debug = 0

class ReaderApp:
    def __init__(self, args, app_status):

        self.current_file_date = datetime.today().date()
        self.lock = asyncio.Lock()
        
        super().__init__()

        # embed the bacpypes BACnet application
        self.app = Application.from_args(args)
        self.app_status = app_status
        self.app.add_object(app_status)
        self.app_state = "active"
        
        self.devices_config = self.load_yaml_config("configs/bacnet_config_201201.yaml")
        
        # Start the openleadr client
        asyncio.create_task(self.dataset_maker())

        # create a task to update the values
        asyncio.create_task(self.update_bacnet_server_values())
        
        # Add the system metrics logging task
        asyncio.create_task(self.log_system_metrics())
        
    async def share_data_to_bacnet_server(self):
        # BACnet server processes
        # not used at the moment but could be if some external
        # platform monitored the state via BACnet
        return self.app_state


    async def update_bacnet_server_values(self):
        # BACnet server processes
        # not used at the moment but could be if some external
        # platform monitored the state via BACnet
        while True:
            await asyncio.sleep(1)
            self.app_status.presentValue = await self.share_data_to_bacnet_server()


    def load_yaml_config(self, filename):
        try:
            with open(filename, 'r') as file:
                config = yaml.safe_load(file)

            for device in config["devices"]:
                device["address"] = Address(device["address"])

                for point in device["points"]:
                    obj_id_parts = point["object_identifier"].split(',')
                    if len(obj_id_parts) == 2:
                        point["object_identifier"] = ObjectIdentifier(f"{obj_id_parts[0]},{int(obj_id_parts[1])}")
                    else:
                        logging.error(f"Invalid object identifier format: {point['object_identifier']}")

            return config

        except Exception as e:
            logging.error(f"Error loading YAML config: {e}")
            raise

    
    async def log_system_metrics(self):
        while True:
            timestamp = datetime.now().isoformat()
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent
            # Add more metrics if needed

            system_metrics = [
                (timestamp, 'Pi_CPU_Usage', cpu_usage),
                (timestamp, 'Pi_Memory_Usage', memory_usage),
                (timestamp, 'Pi_Disk_Usage', disk_usage),
                # Add more metrics here
            ]

            await self.write_to_csv(system_metrics, is_system_metrics=True)
            await asyncio.sleep(3600)
            

    async def write_to_csv(self, data, is_system_metrics=False):
        current_date = datetime.today().date()

        # Create the data and archived directories if they don't exist
        data_dir = "data"
        archived_directory = os.path.join(data_dir, "archived")
        os.makedirs(archived_directory, exist_ok=True)

        # Check if the date has changed
        if current_date != self.current_file_date:
            # Rename and move the existing file to the archived directory
            existing_file_path = os.path.join(data_dir, "bacnet_data.csv")
            if os.path.exists(existing_file_path):
                archived_file_name = f"bacnet_data_{self.current_file_date.strftime('%Y_%m_%d')}.csv"
                archived_file_path = os.path.join(archived_directory, archived_file_name)
                os.rename(existing_file_path, archived_file_path)

            # Update the current file date
            self.current_file_date = current_date

        # File path for the current day
        csv_file_path = os.path.join(data_dir, "bacnet_data.csv")

        # Thread safety attempt with asyncio Lock
        async with self.lock:
            # Check if the file exists and has content
            file_exists = os.path.exists(csv_file_path) and os.path.getsize(csv_file_path) > 0

            async with aiofiles.open(csv_file_path, mode="a", newline="") as file:
                if not file_exists and not is_system_metrics:
                    await file.write(",".join(["Time", "Point Name", "Value"]) + "\n")

                for timestamp, metric_name, metric_value in data:
                    await file.write(",".join([timestamp, metric_name, str(metric_value)]) + "\n")

            logging.info("CSV WRITER DONE!!!")

        
    async def do_read_property_task(self, requests):
        read_values = []
        logging.info(f" requests {requests} ")

        for request in requests:
            try:
                # Destructure the request into its components
                address, object_id, prop_id, array_index, point_name = request

                # Perform the BACnet read property operation
                value = await self.app.read_property(
                    address, object_id, prop_id, array_index
                )
                logging.info(f" Read request {point_name}: {value}")

                # Append the result to the read_values list
                read_values.append((value, point_name))

            except ErrorRejectAbortNack as err:
                logging.error(f" Error while processing READ REQUEST: {err}")
                # Insert "error" in place of the failed read value
                read_values.append(("error", point_name))

            except Exception as e:
                logging.error(f" An unexpected error occurred on READ REQUEST: {e}")
                # Insert "error" in place of the failed read value
                read_values.append(("error", point_name))

        return read_values


    async def read_property_multiple_task(self, address, *args):
        logging.debug(f"args: {args}")

        if len(args) == 1 and isinstance(args[0], tuple):
            args = args[0]

        # Convert args tuple directly to a list without pairing
        args_list = list(args)
        logging.debug(f"args_list: {args_list}")

        # get information about the device from the cache
        device_info = await self.app.device_info_cache.get_device_info(address)

        # using the device info, look up the vendor information
        if device_info:
            vendor_info = get_vendor_info(device_info.vendor_identifier)
        else:
            vendor_info = get_vendor_info(0)

        parameter_list = []
        while args_list:
            # use the vendor information to translate the object identifier,
            # then use the object type portion to look up the object class
            object_identifier = vendor_info.object_identifier(args_list.pop(0))
            object_class = vendor_info.get_object_class(object_identifier[0])
            if not object_class:
                logging.debug(f" unrecognized object type: {object_identifier}")
                return

            # save this as a parameter
            parameter_list.append(object_identifier)

            property_reference_list = []
            while args_list:
                # use the vendor info to parse the property reference
                property_reference = PropertyReference(
                    args_list.pop(0),
                    vendor_info=vendor_info,
                )
                if _debug:
                    logging.debug("    - property_reference: %r", property_reference)

                if property_reference.propertyIdentifier not in (
                    PropertyIdentifier.all,
                    PropertyIdentifier.required,
                    PropertyIdentifier.optional,
                ):
                    property_type = object_class.get_property_type(
                        property_reference.propertyIdentifier
                    )
                    if _debug:
                        logging.debug("    - property_type: %r", property_type)
                        logging.debug("    - property_reference.propertyIdentifier: %r", property_reference.propertyIdentifier)
                    if not property_type:
                        logging.debug(
                            f"unrecognized property: {property_reference.propertyIdentifier}"
                        )
                        return

                # save this as a parameter
                property_reference_list.append(property_reference)

                # crude check to see if the next thing is an object identifier
                if args_list and ((":" in args_list[0]) or ("," in args_list[0])):
                    break

            # save this as a parameter
            parameter_list.append(property_reference_list)


        if not parameter_list:
            await self.response("object identifier expected")
            return

        try:
            
            response = await self.app.read_property_multiple(address, parameter_list)

        except ErrorRejectAbortNack as err:
            if _debug:
                logging.debug("    - exception: %r", err)
            return

        # dump out the results
        for (
            object_identifier,
            property_identifier,
            property_array_index,
            property_value,
        ) in response:
            if property_array_index is not None:
                logging.debug(
                    f" rpm {object_identifier} {property_identifier}[{property_array_index}] {property_value}"
                )
            else:
                logging.debug(
                    f" rpm {object_identifier} {property_identifier} {property_value}"
                )
            if isinstance(property_value, ErrorType):
                logging.debug(
                    f" rpm error - {property_value.errorClass}, {property_value.errorCode}"
                )
        
        return response

    def format_rpm_data(self, rpm_data, timestamp):
        formatted_data = []
        for obj_identifier, prop_identifier, _, value in rpm_data:
            # Extract the object type and instance number
            obj_type, instance = obj_identifier
            point_name = f"{obj_type},{instance}_{prop_identifier}"

            formatted_data.append((timestamp, point_name, value))

        return formatted_data


    async def scrape_device(self, device_config):
        scrape_interval = device_config['scrape_interval']
        read_multiple = device_config.get('read_multiple', False)
        device_address = device_config['address']
        device_name = device_config["device_name"]

        while True:
            if read_multiple:
                # Define device_requests for RPM in the flattened format
                device_requests = []
                for point in device_config['points']:
                    # Assuming point['object_identifier'] is a tuple-like ObjectIdentifier
                    object_type, instance = point['object_identifier']

                    # Format object_type and instance into the required string format
                    object_type_instance_str = f"{object_type},{instance}"

                    # Add to the device_requests
                    device_requests.extend([object_type_instance_str, BACNET_PRESENT_VALUE_PROP_IDENTIFIER])

                # Call read_property_multiple_task with unpacked arguments
                data = await self.read_property_multiple_task(device_address, *device_requests)
                logging.info(f" rpm data: {data}")

                if data is not None:
                    timestamp = datetime.now().isoformat()
                    formatted_data = self.format_rpm_data(data, timestamp)
                    logging.info(f"time: {timestamp}, data: {formatted_data}")

                    await self.write_to_csv(formatted_data, is_system_metrics=False)

            else:
                # Define device_requests for non-RPM
                device_requests = [
                    (device_address, ObjectIdentifier(point['object_identifier']), 
                    BACNET_PRESENT_VALUE_PROP_IDENTIFIER, BACNET_PROPERTY_ARRAY_INDEX, 
                    f"{device_name}_{point['object_name'].lower()}")
                    for point in device_config['points']
                ]
                
                data = await self.do_read_property_task(device_requests)
                logging.info(f" no rpm data: {data}")
                
                if data is not None:
                    timestamp = datetime.now().isoformat()
                    data_with_timestamp = [(timestamp, point_name, value) for value, point_name in data]
                    logging.info(f"time: {timestamp}, data: {data_with_timestamp}")

                    await self.write_to_csv(data_with_timestamp, is_system_metrics=False)
            
            await asyncio.sleep(scrape_interval)


    async def dataset_maker(self):
        tasks = []
        for device_config in self.devices_config["devices"]:
            task = asyncio.create_task(self.scrape_device(device_config))
            tasks.append(task)
        
        await asyncio.gather(*tasks)


async def main():
    args = SimpleArgumentParser().parse_args()
    logging.debug("args: %r", args)

    app_status = BinaryValueObject(
        objectIdentifier=("binaryValue", 1),
        objectName="cloud-dr-server-state",
        presentValue="active",
        statusFlags=[0, 0, 0, 0],
        description="True if app can reach to cloud DR server",
    )

    # instantiate the ReaderApp with test_av and test_bv
    app = ReaderApp(
        args,
        app_status=app_status,
    )
    logging.debug("app: %r", app)

    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        if _debug:
            logging.debug("keyboard interrupt")