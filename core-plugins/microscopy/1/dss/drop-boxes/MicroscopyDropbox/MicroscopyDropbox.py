# -*- coding: utf-8 -*-

"""
@author: Aaron Ponti
"""

import os
import logging

from Processor import Processor


def process(transaction):
    """Dropbox entry point.

    @param transaction, the transaction object
    """

    # Get path to containing folder
    # __file__ does not work (reliably) in Jython
    dbPath = "../core-plugins/microscopy/1/dss/drop-boxes/MicroscopyDropbox"

    # Path to the logs subfolder
    logPath = os.path.join(dbPath, "logs")

    # Make sure the logs subfolder exist
    if not os.path.exists(logPath):
        os.makedirs(logPath)

    # Path for the log file
    logFile = os.path.join(logPath, "log.txt")

    # Set up logging
    logging.basicConfig(filename=logFile, level=logging.DEBUG, 
                        format='%(asctime)-15s %(levelname)s: %(message)s')
    logger = logging.getLogger("Microscopy")

    # Create a Processor
    processor = Processor(transaction, logger)

    # Run
    processor.run()
