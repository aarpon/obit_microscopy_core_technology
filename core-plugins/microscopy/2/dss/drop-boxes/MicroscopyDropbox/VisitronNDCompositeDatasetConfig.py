# -*- coding: utf-8 -*-

"""
Created on Feb 20, 2014

@author: Aaron Ponti
"""

import re
import random
import math
from MicroscopyCompositeDatasetConfig import MicroscopyCompositeDatasetConfig
from VisitronNDMaximumIntensityProjectionGenerationAlgorithm import VisitronNDMaximumIntensityProjectionGenerationAlgorithm
from ch.systemsx.cisd.openbis.dss.etl.dto.api import ChannelColor
from ch.systemsx.cisd.openbis.dss.etl.dto.api import ImageIdentifier
from ch.systemsx.cisd.openbis.dss.etl.dto.api import ImageMetadata
from ch.systemsx.cisd.openbis.dss.etl.dto.api import OriginalDataStorageFormat
from ch.systemsx.cisd.openbis.dss.etl.dto.api import ChannelColorRGB
from ch.systemsx.cisd.openbis.dss.etl.dto.api import Channel
import xml.etree.ElementTree as ET
from GlobalSettings import GlobalSettings
from java.io import BufferedReader
from java.io import File
from java.io import FileReader
from java.util import HashMap
from com.sun.rowset.internal import Row
import string

# Letters array
LETTERS = list(string.ascii_uppercase)

class VisitronNDCompositeDatasetConfig(MicroscopyCompositeDatasetConfig):
    """Image data configuration class for Visitron ND experiments."""

    _DEBUG = True

    # List of metadata attributes obtained either from the settings XML 
    # file generated by the Annotation Tool or returned by 
    # BioFormatsProcessor.getMetadata(asXML=False) 
    # (for all series in the file, sorted by series).
    _allSeriesMetadata = None

    # Number of the series to register (for a multi-series dataset).
    _seriesNum = 0

    # Series indices (since they might not always start from zero and 
    # grow monotonically.
    _seriesIndices = []

    # Logger
    _logger = None

    # Dataset base name
    _basename = ""

    # Metadata folder
    _metadataFolder = ""

    # Maintain a metadata array
    _metadata = []

    # Regular expression patterns
    _pattern = re.compile(r'^(?P<basename>.*?)' +           # Series basename: group 1
                          '(_w(?P<channel>\d.*?))?' +       # Channel number (optional)
                          '(conf(?P<wavelength>\d.*?))?' +  # Wavelength
                          '(_s(?P<series>\d.*?))?' +        # Series number (optional)
                          '(_t(?P<timepoint>\d.*?))?' +     # Time index (optional)
                          '(\.stk|\.tif{1,2})$',            # File extension
                          re.IGNORECASE|re.UNICODE)


    def __init__(self, allSeriesMetadata, seriesIndices, logger, seriesNum=0):
        """Constructor.

        @param allSeriesMetadata: list of metadata attributes generated either
                                  by the Annotation Tool and parsed from the
                                  settings XML file, or from BioFormatsProcessor
                                  and returned via:
                                  BioFormatsProcessor.getMetadataXML(asXML=False)
        @param seriesIndices:     list of known series indices (do not
                                  necessarily need to start at 0 and increase
                                  monotonically by one; could be [22, 30, 32]
        @param seriesNum:         Int Number of the series to register. All
                                  other series in the file will be ignored.
                                  seriesNum MUST BE CONTAINED in seriesIndices.
        @param logger:            logger object
        """

        # Store the logger
        self._logger = logger

        # Store the series metadata
        self._allSeriesMetadata = allSeriesMetadata

        # Store the seriesIndices
        if type(seriesIndices) == str:
             seriesIndices = seriesIndices.split(",")
        self._seriesIndices = map(int, seriesIndices)

        # Store the series number: make sure that it belongs to seriesIndices
        self._seriesNum = int(seriesNum)
        try:
            self._seriesIndices.index(self._seriesNum)
        except:
            raise(Exception("seriesNum (" + str(self._seriesNum) + ") MUST be contained " +
                            "in seriesIndices " + str(self._seriesIndices) + "!"))

        # This is microscopy data
        self.setMicroscopyData(True)

        # Store raw data in original form
        self.setOriginalDataStorageFormat(OriginalDataStorageFormat.UNCHANGED)

        # Set the image library
        self.setImageLibrary("BioFormats")

        # Disable thumbnail generation by ImageMagick
        self.setUseImageMagicToGenerateThumbnails(False)

        # Specify resolution of image representations explicitly
        resolutions = GlobalSettings.ImageResolutions
        if not resolutions:
            self._logger.info("Skipping thumbnails generation.")
            self.setGenerateThumbnails(False)
        else:
            self._logger.info("Creating thumbnails at resolutions: " + str(resolutions))
            self.setGenerateImageRepresentationsUsingImageResolutions(resolutions)
            self.setGenerateThumbnails(True)

        # Set the recognized extensions
        self.setRecognizedImageExtensions(["tif", "tiff", "stk"])

        # Set the dataset type
        self.setDataSetType("MICROSCOPY_IMG")

        # Create representative image (MIP) for the first series only
        if self._seriesIndices.index(self._seriesNum) == 0:
            self.setImageGenerationAlgorithm(
                VisitronNDMaximumIntensityProjectionGenerationAlgorithm(
                    "MICROSCOPY_IMG_THUMBNAIL", 256, 256, "thumbnail.png"))


    def createChannel(self, channelCode):
        """Create a channel from the channelCode with the name as read from
        the file via the MetadataReader and the color (RGB) as read.

        @param channelCode Code of the channel as generated by extractImagesMetadata().
        """

        # Get the indices of series and channel from the channel code
        (seriesIndx, channelIndx) = self._getSeriesAndChannelNumbers(channelCode)

        # Get the channel name
        name = self._getChannelName(seriesIndx, channelIndx)

        # Get the channel color (RGB)
        colorRGB = self._getChannelColor(seriesIndx, channelIndx)
 
        if self._DEBUG:
            self._logger.info("VISITRONNDCOMPOSITEDATASETCONFIG::createChannel(): " +
                              "channel (s = " + str(seriesIndx) + ", c = " +
                              str(channelIndx) + ") has code " + channelCode +
                              ", color (" + str(colorRGB) + " and name " + name)

        # Return the channel with given name and color (the code is set to
        # be the same as the channel name).
        return Channel(channelCode, name, colorRGB)


    def extractImagesMetadata(self, imagePath, imageIdentifiers):
        """Overrides extractImageMetadata method making sure to store
        both series and channel indices in the channel code to be reused
        later to extract color information and other metadata.

        The channel code is in the form SERIES-(\d+)_CHANNEL-(\d+).

        Only metadata for the relevant series number is returned!

        @param imagePath Full path to the file to process
        @param imageIdentifiers Array of ImageIdentifier's

        @see constructor.
        """

        # Info
        self._logger.info("Processing file " + str(imagePath) +
                          " with identifiers " + str(imageIdentifiers))

        # Extract the relevant information from the file name - the image
        # identifiers in this case do not carry any useful information.
        m = self._pattern.match(imagePath)

        if m is None:
            err = "VISITRONNDCOMPOSITEDATASETCONFIG::extractImageMetadata(): " + \
            "unexpected file name " + str(imagePath)
            self._logger.error(err)
            raise Exception(err)

        # Get the extracted info
        fileinfo = m.groupdict() 

        # Extract the series number
        # The series number in the file is 1-based
        if fileinfo["series"] is not None:
            series = int(fileinfo["series"]) - 1
        else:
            self._logger.info("Series number not found: falling back to 0.")
            series = 0

        # Make sure to process only the relevant series
        if series != self._seriesNum:
            return []

        # Get and store the base name
        self._basename = fileinfo['basename']

        # Extract the channel number
        # The channel number in the file name is 1-based
        if fileinfo["channel"] is not None:
            channelNumber = int(fileinfo['channel']) - 1
        else:
            self._logger.info("Channel number not found: falling back to 0.")
            channelNumber = 0

        # Extract the wavelength
        wavelength = fileinfo['wavelength']

        # Extract the timepoint
        # The timepoint number in the file (if defined) is 1-based
        if fileinfo["timepoint"] is not None:
            timepoint = int(fileinfo['timepoint']) - 1
        else:
            self._logger.info("Timepoint not found: falling back to 0.")
            timepoint = 0

        # Inform
        self._logger.info("Current file " + str(imagePath) + " has: " + \
                          "basename = " + str(self._basename) + "; " + \
                          "channelNumber = " + str(channelNumber) + "; " + \
                          "wavelength = " + str(wavelength) + "; " + \
                          "seriesNum = " + str(series) + "; " + \
                          "timepoint = " + str(timepoint))

        # Initialize array of metadata entries
        metaData = []

        # Now process the file indentifiers for this file
        # Iterate over all image identifiers
        for id in imageIdentifiers:

            # Extract the relevant info from the image identifier
            plane = int(id.focalPlaneIndex)

            # Make sure to process only the relevant series
            #if self._seriesNum != -1 and series != self._seriesNum:
            #    continue

            # Build the channel code
            channelCode = "SERIES-" + str(series) + "_CHANNEL-" + str(channelNumber)

            # Initialize a new ImageMetadata object
            imageMetadata = ImageMetadata();

            # Fill in all information
            imageMetadata.imageIdentifier = id
            imageMetadata.seriesNumber = series
            imageMetadata.timepoint = timepoint
            imageMetadata.depth = plane
            imageMetadata.channelCode = channelCode
            imageMetadata.tileNumber = 1  # + self._seriesNum
            imageMetadata.well = "IGNORED"

            # Append metadata for current image
            metaData.append(imageMetadata)

        # Now return the image metadata object in an array
        return metaData


    def _getChannelName(self, seriesIndx, channelIndx):
        """Returns the channel name (from the parsed metadata) for
        a given channel in a given series."
        """

        self._logger.info("Retrieving channel name for " + \
                          "series " + str(seriesIndx) + " and " + \
                          "channel " + str(channelIndx))

        # Get the metadata for the requested series
        metadata = self._allSeriesMetadata[seriesIndx]

        # Try extracting the name for the given series and channel
        try:
            key = "channelName" + str(channelIndx)
            name = metadata[key]
        except KeyError:
            err = "VISITRONNDCOMPOSITEDATASETCONFIG::getChannelName(): " + \
            "Could not create channel name for channel " + str(channelIndx) + \
            " and series " + str(seriesIndx) + "for key = " + \
            key + "  from metadata = " + \
            str(metadata)
            self._logger.error(err)
            raise(Exception(err))

        # In case no name was found, assign default name
        if name == "":
            name = "No name"

        self._logger.info("The channel name is " + name)

        return name


    def _getChannelColor(self, seriesIndx, channelIndx):
        """Returns the channel color (from the parsed metadata) for
        a given channel in a given series."
        """

        # Get the position in the seriesIndices list
        indx = self._seriesIndices.index(int(seriesIndx))

        # Get the metadata for the requested series
        metadata = self._allSeriesMetadata[indx]

        # Get the metadata
        try:
            key = "channelColor" + str(channelIndx)
            color = metadata[key]
        except:
            color = None    
 
        if color is not None:
            # The color is already in the 0 .. 255 range
            color = color.split(",")
            R = int(float(color[0]))
            G = int(float(color[1]))
            B = int(float(color[2]))
        else:
            if channelIndx == 0:
                R = 255
                G = 0
                B = 0
            elif channelIndx == 1:
                R = 0
                G = 255
                B = 0
            elif channelIndx == 2:
                R = 0
                G = 0
                B = 255
            else:
                R = random.randint(0, 255)
                G = random.randint(0, 255)
                B = random.randint(0, 255)


        # Create the ChannelColorRGB object
        colorRGB = ChannelColorRGB(R, G, B)

        # Return it
        return colorRGB


    def _getSeriesAndChannelNumbers(self, channelCode):
        """Extract series and channel number from channel code in
        the form SERIES-(\d+)_CHANNEL-(\d+) to a tuple
        (seriesIndx, channelIndx).

        @param channelCode Code of the channel as generated by extractImagesMetadata().
        """

        p = re.compile("SERIES-(\d+)_CHANNEL-(\d+)")
        m = p.match(channelCode)
        if m is None or len(m.groups()) != 2:
            err = "YOUSCOPEEXPERMENTCOMPOSITEDATASETCONFIG::_getSeriesAndChannelNumbers(): " + \
            "Could not extract series and channel number!"
            self._logger.error(err)
            raise Exception(err)

        # Now assign the indices
        seriesIndx = int(m.group(1))
        channelIndx = int(m.group(2))

        if self._DEBUG:
            self._logger.info("Current channel code " + channelCode + \
                              " corresponds to series = " + str(seriesIndx) + \
                              " and channel = " + str(channelIndx))

        # Return them
        return seriesIndx, channelIndx
