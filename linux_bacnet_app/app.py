from bacpypes3.argparse import SimpleArgumentParser
from bacpypes3.local.binary import BinaryValueObject
from bacpypes3.app import Application
from bacpypes3.apdu import ErrorRejectAbortNack
from bacpypes3.local.binary import BinaryValueObject

import asyncio
import os
import asyncio
import logging
import aiofiles
from datetime import datetime

from points import *

# examples args for bacpypes3. Run like:
# $ python3 app.py --name Slipstream --instance 3056672 --address 10.7.6.201/24:47820


logging.basicConfig(level=logging.INFO)  

_debug = 0

class ReaderApp:
    def __init__(self, args, app_status):

        
        super().__init__()

        # embed the bacpypes BACnet application
        self.app = Application.from_args(args)
        self.app_status = app_status
        self.app.add_object(app_status)
        self.app_state = "active"
        
        # Start the openleadr client
        asyncio.create_task(self.dataset_maker())

        # create a task to update the values
        asyncio.create_task(self.update_bacnet_server_values())
        
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

    async def write_to_csv(self, data, time):
        
        data_dir = 'data'
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        csv_file_path = os.path.join(data_dir, 'bacnet_data.csv')

        # Check if the file exists and has content
        file_exists = os.path.exists(csv_file_path) and os.path.getsize(csv_file_path) > 0

        async with aiofiles.open(csv_file_path, mode='a', newline='') as file:
            # Write the headers if the file is new
            if not file_exists:
                await file.write(','.join(['Time', 'Point Name', 'Value']) + '\n')

            # Write the scraped data
            for value, point_name in data:
                await file.write(','.join([time, point_name, str(value)]) + '\n')

        logging.info(" CSV WRITER DONE!!!")
        
    async def do_read_property_task(self, requests):
        read_values = []

        for request in requests:
            try:
                # Destructure the request into its components
                address, object_id, prop_id, array_index, point_name = request
                
                logging.info(" {address} {point_name} GO!")
                
                if _debug:
                    logging.info(f" {address} \n {object_id} \n {prop_id} \n {array_index} \n {point_name}")

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
        device_address = device_config['address']
        scrape_interval = device_config['scrape_interval']
        device_requests = [
            (device_address, point_obj, BACNET_PRESENT_VALUE_PROP_IDENTIFIER, 
            BACNET_PROPERTY_ARRAY_INDEX, f"{device_name}_{point_name.lower()}")
            for point_name, point_obj in device_config['points']
        ]

        while True:
            data = await self.do_read_property_task(device_requests)
            time = datetime.now().isoformat()
            logging.info(f"time: {time}, data: {data}")
            await self.write_to_csv(data, time)
            await asyncio.sleep(scrape_interval)

    async def dataset_maker(self):
        tasks = []
        for device, config in devices.items():
            task = asyncio.create_task(self.scrape_device(device, config))
            tasks.append(task)
        
        await asyncio.gather(*tasks)


async def main():
    args = SimpleArgumentParser().parse_args()
    if _debug:
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
    if _debug:
        logging.debug("app: %r", app)

    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        if _debug:
            logging.debug("keyboard interrupt")
