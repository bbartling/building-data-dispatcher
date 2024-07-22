import asyncio
import aiohttp
import logging
import os
from datetime import datetime
import psutil
import tomllib
import sqlite3
from typing import List, Dict, Any

logging.basicConfig(level=logging.DEBUG)

_debug = 0

class ReaderApp:
    def __init__(self, config_dir: str):
        self.configs = self.load_all_configs(config_dir)
        self.db_connection = sqlite3.connect('bacnet_data.db')
        self.db_cursor = self.db_connection.cursor()

        # Start the tasks
        asyncio.create_task(self.dataset_maker())

    def load_all_configs(self, directory: str) -> List[Dict[str, Any]]:
        configs = []
        for filename in os.listdir(directory):
            if filename.endswith(".toml"):
                try:
                    with open(os.path.join(directory, filename), "rb") as f:
                        config = tomllib.load(f)
                        configs.append(config)
                except Exception as e:
                    logging.error(f"Error loading TOML config '{filename}': {e}")
        return configs

    async def fetch_data(self, session: aiohttp.ClientSession, device_instance: int, points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/bacnet/read-multiple"
        payload = {
            "device_instance": device_instance,
            "requests": [{"object_identifier": p["object_identifier"], "property_identifier": p["property_identifier"]} for p in points]
        }
        headers = {
            "accept": "application/json",
            "Authorization": "Basic YmVuOmJlbg==",  # Replace with actual base64 encoded credentials
            "Content-Type": "application/json"
        }
        
        async with session.post(url, json=payload, headers=headers) as response:
            return await response.json()

    async def save_to_sql(self, data: List[Tuple[str, str, Any]], is_system_metrics=False):
        timestamp = datetime.now().isoformat()
        for metric_name, value in data:
            self.db_cursor.execute('''
                INSERT INTO bacnet_readings (timestamp, point_name, value)
                VALUES (?, ?, ?)
            ''', (timestamp, metric_name, value))
        
        self.db_connection.commit()

    async def scrape_device(self, session: aiohttp.ClientSession, device: Dict[str, Any]):
        interval = self.config["scrape_interval"]
        while True:
            try:
                result = await self.fetch_data(session, device["device_instance"], device["points"])
                if result['success']:
                    timestamp = datetime.now().isoformat()
                    formatted_data = [
                        (timestamp, f"{device['device_instance']}_{point['description']}", request['value'])
                        for request, point in zip(result['data']['requests'], device["points"])
                    ]
                    await self.save_to_sql(formatted_data, is_system_metrics=False)
                else:
                    logging.error(f"Device {device['device_instance']} error: {result.get('message', 'Unknown error')}")
            except Exception as e:
                logging.error(f"Error reading device {device['device_instance']}: {e}")

            await asyncio.sleep(interval)

    async def dataset_maker(self):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for config in self.configs:
                for device in config["devices"]:
                    tasks.append(asyncio.create_task(self.scrape_device(session, device)))
            await asyncio.gather(*tasks)


async def main():
    config_dir = "configs"  # Directory containing all TOML config files
    app = ReaderApp(config_dir)
    await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        if _debug:
            logging.debug("keyboard interrupt")
