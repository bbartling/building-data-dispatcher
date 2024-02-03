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
The generated YAML file contains a structured representation of the BACnet device's points. The structure includes:

* The BACnet device address.
* Device identifier.
* A list of points with their BACnet object identifiers and names.
* Default scrape interval and read multiple settings.

Example YAML content:
```bash
devices:
- address: '12345:2'
  device_identifier: '201201'
  scrape_interval: 60
  read_multiple: true
  points:
    - object_identifier: 'analog-input,1'
      object_name: 'tempUoOne10k'
    - object_identifier: 'analog-input,2'
      object_name: 'tempUoTwoBalco'
    # ... more points ...

```

## TODO is make readme for `app.py`