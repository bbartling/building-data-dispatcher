# Linux app scripts

The `tester.py` script is designed to interact with BACnet devices and generate a YAML configuration file that outlines the structure and attributes of the discovered BACnet points. This script is particularly useful for setting up and initializing the environment for BACnet applications.

## **Running the Script**
To start the script, run the following command in your terminal:

```bash
python3 tester.py --debug
```

This command initiates the BACpypes console with the specified IP address and subnet mask, enabling debug mode for detailed output. If you need a unique port number pass in `--address 10.7.6.201/24:47820`

## Using the BACpypes Console
* `> help` to view the available commands for basic read, writing, and testing the remote BACnet thru SSH.

## Generating the YAML Configuration File
To generate the YAML configuration file for a specific BACnet device, use the `save_device_config` command followed by the device instance ID. For example:

```bash
> save_device_config 201201
```

This command triggers the discovery of BACnet points associated with the device having instance ID `201201`. The script then:

1. Connects to the specified BACnet device.
2. Retrieves the list of objects and their respective names.
3. Saves this information in a YAML file, named `bacnet_config_201201.yaml`, under the `configs` directory.


## YAML File Structure
The generated YAML file contains a structured representation of the BACnet device's points which should be trimmed down and customized with a text editor. The structure includes:

* The BACnet device address.
* Device identifier.
* A list of points with their BACnet object identifiers and names.
* Default scrape interval and BACnet read multiple settings. Recommended to use BACnet read multiple if scraping lots of points and not less than a 60 second scrape interval especially if there is a large site with lots of points.
* Trim points scrape down to only useful data where each `point` needs a matching `object_identifier` and `object_name`.
* Inspect each row of the YAML file `points:` for an `ERROR` which can happen occasionally bacpypes may throw a `bacpypes3.errors.InvalidTag` when doing a point discovery on a device.

Example YAML content:
```bash
devices:
- address: '12:40'
  device_identifier: '601040'
  device_name: MTR-01 BACnet
  points:
  - object_identifier: analog-input,8
    object_name: Outlet Setp. 1
  - object_identifier: analog-input,9
    object_name: Outlet Temp. 1
  - object_identifier: analog-input,10
    object_name: Inlet Temp. 1
  - object_identifier: analog-input,11
    object_name: Flue1/Pool Temp.
  - object_identifier: analog-input,11
    object_name: Firing Rate 1
  read_multiple: true
  scrape_interval: 600
```

## TODO is make readme for `app.py`