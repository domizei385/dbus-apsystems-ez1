#!/usr/bin/env python
import asyncio
import logging
import configparser
import os

from APsystemsEZ1 import APsystemsEZ1M

async def main():
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO,
                        handlers=[
                            logging.FileHandler(
                                "%s/current.log" % (os.path.dirname(os.path.realpath(__file__)))),
                            logging.StreamHandler()
                        ])

    data = await _getData()

    logging.info("data from apsystems:")
    logging.info(data)

async def _getData():
    config = await _getConfig()
    address = config['DEFAULT']['Address']
    port = int(config['DEFAULT']['Port'])

    logging.info("config...")
    logging.info(address)
    logging.info(port)

    client = APsystemsEZ1M(ip_address=address, port=port)

    acEnergyForward = await client.get_total_energy_today()
    acPower = await client.get_total_output()

    return {
        "acEnergyForward": acEnergyForward,
        "acPower": acPower
    }

async def _getConfig():
    config = configparser.ConfigParser()
    config.read("%s/config.ini" %
                (os.path.dirname(os.path.realpath(__file__))))
    return config

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
