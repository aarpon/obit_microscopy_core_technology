# -*- coding: utf-8 -*-

"""
@author: Aaron Ponti
"""

import os

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

    # Make sure the logs subforder exist
    if not os.path.exists(logPath):
        os.makedirs(logPath)

    # Path for the log file
    logFile = os.path.join(logPath, "registration_log.txt")

    # Create a Processor
    processor = Processor(transaction, logFile)

    # Run
    processor.run()
