#!/usr/bin/env python
import asyncio
# import normal packages
import platform
import threading
import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from APsystemsEZ1 import APsystemsEZ1M

if sys.version_info.major == 2:
    import gobject
else:
    from gi.repository import GLib as gobject
import sys
import time
from datetime import datetime
import configparser  # for config/ini file

# our own packages from victron
sys.path.insert(1, os.path.join(os.path.dirname(__file__),
                '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))
from vedbus import VeDbusService

class DbusApSystemsEZ1Service:
    def __init__(self, servicename, paths, productname='ApSystems EZ1'):
        self.config = self._getConfig()
        deviceinstance = int(self.config['DEFAULT']['Deviceinstance'])
        customname = self.config['DEFAULT']['CustomName']

        self._dbusservice = VeDbusService(
            "{}.tcp_{:02d}".format(servicename, deviceinstance))
        self._paths = paths

        logging.debug("%s /DeviceInstance = %d" %
                      (servicename, deviceinstance))

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
        self._dbusservice.add_path(
            '/Mgmt/ProcessVersion', 'Unknown version, and running on Python ' + platform.python_version())
        # self._dbusservice.add_path('/Mgmt/Connection', connection)

        # Create the mandatory objects
        self._dbusservice.add_path('/DeviceInstance', deviceinstance)
        # self._dbusservice.add_path('/ProductId', 16) # value used in ac_sensor_bridge.cpp of dbus-cgwacs
        # id assigned by Victron Support from SDM630v2.py
        self._dbusservice.add_path('/ProductId', 0xFFFF)
        self._dbusservice.add_path('/ProductName', productname)
        self._dbusservice.add_path('/CustomName', customname)
        self._dbusservice.add_path('/Connected', 1)
        self._dbusservice.add_path('/LastConnected', None)

        self._dbusservice.add_path('/Latency', None)
        self._dbusservice.add_path(
            '/HardwareVersion', self._getHWVersion())
        self._dbusservice.add_path(
            '/Position', int(self.config['DEFAULT']['Position']))
        self._dbusservice.add_path('/Serial', self._getSerial())
        self._dbusservice.add_path('/UpdateIndex', 0)
        # Dummy path so VRM detects us as a PV-inverter.
        self._dbusservice.add_path('/StatusCode', 0)

        # add path values to dbus
        for path, settings in self._paths.items():
            self._dbusservice.add_path(
                path, settings['initial'], gettextcallback=settings['textformat'], writeable=True, onchangecallback=self._handlechangedvalue)

        # last update
        self._lastUpdate = 0

        # add _update function 'timer'
        # pause x ms before the next request
        self._updateInterval = int(self.config['DEFAULT']['UpdateInterval'])

    async def start(self):
        address = self.config['DEFAULT']['Address']
        port = int(self.config['DEFAULT']['Port'])

        self._client = APsystemsEZ1M(ip_address=address, port=port)

        loop = asyncio.get_event_loop()
        data_update = loop.create_task(self._update_loop())
        loop.create_task(self._signOfLife())
        await asyncio.gather(data_update)

    async def _update_loop(self):
        while True:
            result = await self._update()
            await asyncio.sleep(self._updateInterval if result else 60)

    def _getSerial(self):
        return self.config['DEFAULT']['Serial']

    def _getHWVersion(self):
        return 1.0

    def _getConfig(self):
        config = configparser.ConfigParser()
        config.read("%s/config.ini" %
                    (os.path.dirname(os.path.realpath(__file__))))
        return config

    def _getSignOfLifeInterval(self):
        value = self.config['DEFAULT']['SignOfLifeLog']

        if not value:
            value = 0

        return int(value)

    async def _getData(self):
        try:
            data = await self._client.get_output_data()
            acEnergyForward = float(data.e1 + data.e2) if data else None
            acPower = float(data.p1 + data.p2) if data else None
        except Exception as e:
            return None
            #logging.critical('Error at %s', '_update', exc_info=e)

        return {
            "acEnergyForward": acEnergyForward,
            "acPower": acPower,
            "acVoltage": 0.0,
            "acCurrent": 0.0
        }
    
    async def _signOfLife(self):
        while True:
            logging.info("--- Start: sign of life ---")
            logging.info("Last _update() call: %s" % (self._lastUpdate))
            logging.info("Last '/Ac/Power': %s" % (self._dbusservice['/Ac/Power']))
            logging.info("--- End: sign of life ---")
            await asyncio.sleep(self._getSignOfLifeInterval())

    async def _update(self):
        try:
            # get data from apsystems
            data = await self._getData()

            phase = str(self.config['DEFAULT']['Phase'])
            # send data to DBus
            pre = '/Ac/' + phase

            self._dbusservice[pre + '/Voltage'] = data['acVoltage'] if data else 0.0
            self._dbusservice[pre + '/Current'] = data['acCurrent']  if data else 0.0
            self._dbusservice[pre + '/Power'] = data['acPower']  if data else 0.0
            self._dbusservice['/Connected'] = 1 if data else 0
            self._dbusservice['/Ac/Voltage'] = self._dbusservice[pre + '/Voltage']
            self._dbusservice['/Ac/Current'] = self._dbusservice[pre + '/Current']
            self._dbusservice['/Ac/Power'] = self._dbusservice[pre + '/Power']
            if data:
                self._dbusservice[pre + '/Energy/Forward'] = data['acEnergyForward']
                self._dbusservice['/Ac/Energy/Forward'] = self._dbusservice[pre + '/Energy/Forward']
                # update lastupdate vars
                self._lastUpdate = time.time()
                now = datetime.now()
                self._dbusservice['/LastConnected'] = now.strftime("%Y-%m-%d %H:%M:%S")

            # logging
            logging.debug("Consumption (/Ac/Power): %s" %(self._dbusservice['/Ac/Power']))
            logging.debug("Forward (/Ac/Energy/Forward): %s" %(self._dbusservice['/Ac/Energy/Forward']))
            logging.debug("---")

        except Exception as e:
            logging.critical('Error at %s', '_update', exc_info=e)

            try:
                if self._lastUpdate < (time.time() - 5 * 60):
                    self._dbusservice['/Connected'] = 0
            except Exception as e:
                logging.critical('Error at %s', '_update', exc_info=e)
 
        try:
            # increment UpdateIndex - to show that new data is available
            index = self._dbusservice['/UpdateIndex'] + 1  # increment index
            if index > 255:   # maximum value of the index
                index = 0       # overflow from 255 to 0
            self._dbusservice['/UpdateIndex'] = index
        except Exception as e:
            logging.critical('Error at %s', '_update', exc_info=e)

        # return true, otherwise add_timeout will be removed from GObject - see docs http://library.isr.ist.utl.pt/docs/pygtk2reference/gobject-functions.html#function-gobject--timeout-add
        return True

    def _handlechangedvalue(self, path, value):
        logging.debug("someone else updated %s to %s" % (path, value))
        return True  # accept the change

async def main():
    # configure logging
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO,
                        handlers=[
                            RotatingFileHandler("%s/current.log" % (os.path.dirname(os.path.realpath(__file__))), maxBytes=1024*1024, backupCount=5),
                            logging.StreamHandler()
                        ])

    try:
        logging.info("Start")

        from dbus.mainloop.glib import DBusGMainLoop
        # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
        DBusGMainLoop(set_as_default=True)

        # formatting
        _kwh = lambda p, v: (str(round(v, 2)) + ' kWh')
        _a = lambda p, v: (str(round(v, 1)) + ' A')
        _w = lambda p, v: (str(round(v, 1)) + ' W')
        _v = lambda p, v: (str(round(v, 1)) + ' V')

        # start our main-service
        inverter = DbusApSystemsEZ1Service(
            servicename='com.victronenergy.pvinverter',
            paths={
                # energy produced by pv inverter
                '/Ac/Energy/Forward': {'initial': None, 'textformat': _kwh},
                '/Ac/Power': {'initial': 0.0, 'textformat': _w},
                '/Ac/Current': {'initial': 0.0, 'textformat': _a},
                '/Ac/Voltage': {'initial': 0.0, 'textformat': _v},

                '/Ac/L1/Voltage': {'initial': 0.0, 'textformat': _v},
                '/Ac/L2/Voltage': {'initial': 0.0, 'textformat': _v},
                '/Ac/L3/Voltage': {'initial': 0.0, 'textformat': _v},
                '/Ac/L1/Current': {'initial': 0.0, 'textformat': _a},
                '/Ac/L2/Current': {'initial': 0.0, 'textformat': _a},
                '/Ac/L3/Current': {'initial': 0.0, 'textformat': _a},
                '/Ac/L1/Power': {'initial': 0.0, 'textformat': _w},
                '/Ac/L2/Power': {'initial': 0.0, 'textformat': _w},
                '/Ac/L3/Power': {'initial': 0.0, 'textformat': _w},
                '/Ac/L1/Energy/Forward': {'initial': None, 'textformat': _kwh},
                '/Ac/L2/Energy/Forward': {'initial': None, 'textformat': _kwh},
                '/Ac/L3/Energy/Forward': {'initial': None, 'textformat': _kwh},
            })
        
        mainloop = gobject.MainLoop()

        def runMainloop():
            mainloop.run()
        mainloopThread = threading.Thread(name='mainloop', target=runMainloop)
        mainloopThread.setDaemon(True)
        mainloopThread.start()
        
        logging.info('Connected to dbus, and switching over to gobject.MainLoop() (= event based)')
        await inverter.start()
    except Exception as e:
        logging.critical('Error at %s', 'main', exc_info=e)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
