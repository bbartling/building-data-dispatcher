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

from points import *
import yaml

# examples args for bacpypes3. Run like:
# $ python3 app.py --name Slipstream --instance 3056672 --address 10.7.6.201/24:47820

# Define BACnet properties
BACNET_PRESENT_VALUE_PROP_IDENTIFIER = "present-value"
BACNET_PROPERTY_ARRAY_INDEX = None

logging.basicConfig(level=logging.INFO)  

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

    
    async def log_system_metrics(self):
        while True:
            timestamp = datetime.now().isoformat()
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent
            # Add more metrics if needed

            system_metrics = [
                (timestamp, 'CPU Usage', cpu_usage),
                (timestamp, 'Memory Usage', memory_usage),
                (timestamp, 'Disk Usage', disk_usage),
                # Add more metrics here
            ]

            await self.write_to_csv(system_metrics, is_system_metrics=True)
            await asyncio.sleep(600)


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
        print(f" requests {requests} ")

        for request in requests:
            try:
                # Destructure the request into its components
                address, object_id, prop_id, array_index, point_name = request
                
                logging.info(f" {address} {point_name} GO!")

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


    async def scrape_device(self, device_name, device_config):
        scrape_interval = device_config['scrape_interval']
        read_multiple = device_config.get('read_multiple', False)
        device_address = device_config['address']

        while True:
            if read_multiple:
                print("passing on this device service not implemented yet...")
            else:
                device_requests = [
                    (device_address, ObjectIdentifier(point['object_identifier']), 
                    BACNET_PRESENT_VALUE_PROP_IDENTIFIER, BACNET_PROPERTY_ARRAY_INDEX, 
                    f"{device_name}_{point['object_name'].lower()}")
                    for point in device_config['points']
                ]
                data = await self.do_read_property_task(device_requests)

            if data is not None:
                timestamp = datetime.now().isoformat()
                data_with_timestamp = [(timestamp, point_name, value) for value, point_name in data]
                logging.info(f"time: {timestamp}, data: {data_with_timestamp}")

                await self.write_to_csv(data_with_timestamp, is_system_metrics=False)
                
            await asyncio.sleep(scrape_interval)
            

    async def dataset_maker(self):
        tasks = []
        for device_config in self.devices_config["devices"]:
            device_name = device_config["device_identifier"]
            task = asyncio.create_task(self.scrape_device(device_name, device_config))
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