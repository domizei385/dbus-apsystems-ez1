# dbus-apsystems-ez1
Integrate APsystems EZ1 Inverter into Victron Energies Venus OS

## Purpose
With the scripts in this repo it should be easy possible to install, uninstall, restart a service that connects the APsystems EZ1 Inverter to the VenusOS and GX devices from Victron.
This repo is based on the great work of @vikt0rm and others.

## Motivation
This repository is a modification of https://github.com/vikt0rm/dbus-shelly-1pm-pvinverter. 

## How it works

### Details / Process
As mentioned above the script is inspired by @fabian-lauer dbus-shelly-3em-smartmeter implementation.
So what is the script doing:
- Running as a service
- connecting to DBus of the Venus OS `com.victronenergy.pvinverter.http_{DeviceInstanceID_from_config}`
- After successful DBus connection APsystems EZ1 Inverter is called via api and values are being published on DBus
- The device system time gets updated to allow daly production reset
- Serial is taken from the config file, auto detection is possible but not implemented
- Paths are added to the DBus with default value 0 - including some settings like name, etc
- After that a "loop" is started which pulls APsystems EZ1 Inverter data every x seconds
- The interval can be configured through the config file


### Pictures
![VRM Dashboard](img/vrm-dashboard.png)
![Tile Overview](img/venus-os-overview.png)
![Remote Console - Device List](img/venus-os-devicelist.png) 
![SmartMeter - Values](img/venus-os-device.png)


## Install & Configuration
### Get the code
Just grap a copy of the main branche and copy them to a folder under `/data/` e.g. `/data/dbus-apsystems-ez1`.
After that call the install.sh script.

The following script should do everything for you:
```
wget https://github.com/domizei385/dbus-apsystems-ez1/archive/refs/heads/main.zip
unzip main.zip && mv dbus-apsystems-ez1-main /data/dbus-apsystems-ez1 && rm main.zip
cd /data/dbus-apsystems-ez1/
chmod a+x install.sh
./install.sh
```
⚠️ Check configuration after that - because service is already installed an running and with wrong connection data (host, username, pwd) you will spam the log-file

### Change config.ini
Within the project there is a file `/data/dbus-apsystems-ez1/config.ini` - just change the values - most important is the deviceinstance, custom name and phase under "DEFAULT" and host, username and password in section "ONPREMISE". More details below:

| Section  | Config vlaue | Explanation                                                                                                                       |
| ------------- | ------------- |-----------------------------------------------------------------------------------------------------------------------------------|
| DEFAULT  | Address | IP or hostname of APsystems EZ1 Inverter                                                                                          |
| DEFAULT  | Port | The port on which APsystems EZ1 Inverter API is running                                                                           |
| DEFAULT  | Serial | The serial number of the logger integrated in the inverter                                                                        |
| DEFAULT  | Phase | Valid values L1, L2 or L3: represents the phase where pv inverter is feeding in                                                   |
| DEFAULT  | SignOfLifeLog  | Time in minutes how often a status is added to the log-file `current.log` with log-level INFO                                     |
| DEFAULT  | Deviceinstance | Unique ID identifying the APsystems EZ1 Inverter in Venus OS                                                                                 |
| DEFAULT  | CustomName | Name shown in Remote Console (e.g. name of pv inverter)                                                                           |
| DEFAULT  | Position | Valid values 0, 1 or 2: represents where the inverter is connected (0=AC input 1; 1=AC output; 2=AC input 2)                      |
| DEFAULT  | UpdateInterval | The interval how often the data is read from the inverter in seconds. The inverter itself accumulates the values every 5 minutes. |

### Testing configuration
If you encounter any issue please test your settings in config.ini with:
```
cd /data/dbus-apsystems-ez1/
chmod a+x test-config.py
./test-config.py
```

There should be no error message but some JSON like output with data fetched from your inverter.

## Used documentation
- https://github.com/victronenergy/venus/wiki/dbus#pv-inverters   DBus paths for Victron namespace
- https://github.com/victronenergy/venus/wiki/dbus-api   DBus API from Victron
- https://www.victronenergy.com/live/ccgx:root_access   How to get root access on GX device/Venus OS
