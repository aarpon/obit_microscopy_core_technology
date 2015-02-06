# -*- coding: utf-8 -*-

"""
@author: Aaron Ponti
"""

import os
import logging
import re

from ch.systemsx.cisd.openbis.common.hdf5 import HDF5Container

from Processor import Processor


def process(transaction):
    """Dropbox entry point.

    @param transaction, the transaction object
    """

    # Disabling HDF5 caching
    HDF5Container.disableCaching()

    # Get path to containing folder
    # __file__ does not work (reliably) in Jython
    dbPath = "../core-plugins/microscopy/1/dss/drop-boxes/MicroscopyDropbox"

    # Path to the logs subfolder
    logPath = os.path.join(dbPath, "logs")

    # Make sure the logs subforder exist
    if not os.path.exists(logPath):
        os.makedirs(logPath)

    # Path for the log file
    logFile = os.path.join(logPath, "registration_log.txt")

    # Set up logging
    logger = logging.getLogger('MicroscopyDropbox')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logFile)
    fh.setLevel(logging.DEBUG)
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(format)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Create a Processor
    processor = Processor(transaction, logger)

    # Run
    processor.run()
