import os
import logging
from sets import Set

from ch.systemsx.cisd.openbis.dss.etl.dto.api.impl import MaximumIntensityProjectionGenerationAlgorithm

_DEBUG = True


def setUpLogging():
    """Set up logging."""

    # Get path to containing folder
    # __file__ does not work (reliably) in Jython
    dbPath = "../core-plugins/microscopy/4/dss/maintenance-tasks/microscopy_thumbnails_creation"

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
    logger = logging.getLogger()
    return logger


def _get_series_num(logger):
    """Retrieve series numbers."""

    series_numbers = Set()
    for image_info in image_data_set_structure.getImages():

        if logger is not None:
            logger.info("ImageInfo channel code: " + str(image_info.getChannelCode()))

        series_numbers.add(image_info.tryGetSeriesNumber())

    if logger is not None:
        logger.info("Series numbers: " + str(series_numbers))

    return series_numbers.pop()


def process(transaction, parameters, tableBuilder):
    """Maintenance task entry point."""

    # Set up logging
    logger = None
    if _DEBUG:
        logger = setUpLogging()

    # Get series number
    series_num = int(_get_series_num(logger))

    # Thumbnails are created only for the first series
    if series_num == 0:
        image_config.setImageGenerationAlgorithm(
            MaximumIntensityProjectionGenerationAlgorithm(
                "MICROSCOPY_IMG_THUMBNAIL", 256, 256, "thumbnail.png"))
        if logger is not None:
            logger.info("Series number: " + str(series_num) + ": requested thumbnail generation.")

    else:
        if logger is not None:
            logger.info("Series number: " + str(series_num) + ": skipped thumbnail generation.")
