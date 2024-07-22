# Building Data Dispatcher

This project is an asynchronous data collection tool that uses client HTTP requests to gather telemetry data from BACnet devices. It is capable of scaling from single to multiple buildings through a VPN connection to a remote BACnet network. Designed to work with an HTTP server running inside a building's intranet alongside BACnet devices and behind the firewall, it integrates seamlessly with the [bacpypes3RcpServer](https://github.com/bbartling/bacpypes3RcpServer/tree/develop). The collected data is stored in an SQLite database and organized using the Brick schema ontology, providing a standardized way to represent metadata and relationships within building systems.

## Features

- Asynchronously collect telemetry data from BACnet devices across multiple buildings.
- Scales from single to multiple buildings through a VPN connection.
- Stores telemetry data in an SQLite database using the Brick schema ontology.
- Logs system metrics asynchronously.
- Designed to work with a remote HTTP server inside the building's intranet.

## Directory Structure

- `app.py`: The main application script.
- `config.toml`: A sample configuration file.
- `configs/`: Directory containing TOML configuration files for each building.
- `data/`: Directory for storing CSV data.
  - `archived/`: Subdirectory for archived CSV files.
- `bacnet_data.db`: SQLite database file for BACnet readings.
- `README.md`: Project overview and setup instructions.

## Setup

1. Install dependencies:
    ```sh
    pip install aiohttp aiofiles psutil tomllib sqlite3
    ```

2. Place the TOML configuration files for each building in the `configs/` directory.

3. Run the application:
    ```sh
    python app.py
    ```

## Configuration

Each building should have its own TOML file in the `configs/` directory. The configuration file should define the building details, devices, and points to be monitored. Example:

```toml
base_url = "http://100.234.23.125:5000"
scrape_interval = 60

[building]
name = "Building A"
location = "Campus 1"

[[devices]]
device_instance = 10
brick_class = "VAV"
location = "Room 101"
feeds = ["AHU1"]

[[devices.points]]
object_identifier = "analog-input,1019"
property_identifier = "present-value"
description = "Discharge Air Temperature (DA-T)"
brick_class = "Discharge_Air_Temperature_Sensor"
```

## Logging
Data is saved to an SQLite database (bacnet_data.db) for testing purposes but a production app would require a time series database.


```bash
my_project/
├── app.py
├── setup_db.py
├── configs/
│   ├── building_A.toml
│   ├── building_B.toml
│   └── building_C.toml
├── bacnet_data.db
└── README.md
```

## TODO

 - [ ] Make sure Brick is setup correctly that the ontology is being followed correctly
 - [ ] Test out on a few real buildings to collect a little data
 - [ ] Test out on Open-FDD for running fault rules on collected data
 - [ ] Update to a Time Series DB?
 
## License
MIT License

Copyright (c) 2024 Ben Bartling

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

ADDITIONAL CYBERSECURITY NOTICE: Users are encouraged to apply the highest level of cybersecurity, OT, IoT, and IT measures when using this software. The authors and copyright holders disclaim any liability for cybersecurity breaches, mechanical equipment damage, financial damage, or loss of life arising from the use of the Software. Users assume full responsibility for ensuring the secure deployment and operation of the Software in their environments.
