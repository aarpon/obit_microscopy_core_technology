# -*- coding: utf-8 -*-

"""
Created on Feb 20, 2014

@author: Aaron Ponti
"""

import re
from MicroscopyCompositeDatasetConfig import MicroscopyCompositeDatasetConfig
from ch.systemsx.cisd.openbis.dss.etl.dto.api import ChannelColor
from ch.systemsx.cisd.openbis.dss.etl.dto.api import ImageIdentifier
from ch.systemsx.cisd.openbis.dss.etl.dto.api import ImageMetadata
from ch.systemsx.cisd.openbis.dss.etl.dto.api import OriginalDataStorageFormat
from ch.systemsx.cisd.openbis.dss.etl.dto.api import ChannelColorRGB
from ch.systemsx.cisd.openbis.dss.etl.dto.api import Channel
import xml.etree.ElementTree as ET


class LeicaTIFFSeriesCompositeDatasetConfig(MicroscopyCompositeDatasetConfig):
    """Image data configuration class for Leica TIFF series."""

    _DEBUG = False

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

    # Regular expression pattern
    _pattern = re.compile("^(.*?)" + \
                          "((_Series|_s)(\d.*?))?" + \
                          "(_t(\d.*?))?" + \
                          "_z(\d.*?)" + \
                          "_ch(\d.*?)" + \
                          "\.tif{1,2}$", re.IGNORECASE)

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
            raise("seriesNum (" + str(self._seriesNum) + ") MUST be contained " + \
                  "in seriesIndices " + str(self._seriesIndices) + "!")

        # This is microscopy data
        self.setMicroscopyData(True)

        # Store raw data in original form
        self.setOriginalDataStorageFormat(OriginalDataStorageFormat.UNCHANGED)

        # Set the image library
        self.setImageLibrary("BioFormats")

        # Disable thumbnail generation by ImageMagick
        self.setUseImageMagicToGenerateThumbnails(False)

        # Enable thumbnail generation
        self.setGenerateThumbnails(True)

        # Specify thumbnail resolution explicitly
        resolutions = ['128x128', '256x256']
        self.setGenerateImageRepresentationsUsingImageResolutions(resolutions)
        # self.setGenerateImageRepresentationsUsingScaleFactors([0.25, 0.5])

        # Set the recognized extensions -- currently just tif(f)
        self.setRecognizedImageExtensions(["tif", "tiff"])

        # Set the dataset type
        self.setDataSetType("MICROSCOPY_IMG")


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
            self._logger.info("LEICATIFFSERIESCOMPOSITEDATASETCONFIG::createChannel(): " + 
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

        # Extract the relevant information from the file name - the image
        # identifiers in this case do not carry any useful information.
        m = self._pattern.match(imagePath)

        if m is None:
            err = "MICROSCOPYCOMPOSITEDATASETCONFIG::extractImageMetadata(): " + \
            "unexpected file name " + str(imagePath)
            self._logger.error(err)
            raise Exception(err)

        # Get and store the base name
        basename = m.group(1)
        if self._basename == "" or self._basename != basename:
            self._basename = basename

        # The series number is not always defined in the file name.
        # In the regex, the group(2) optionally matches _s{digits};
        # in case group(2) is not None, the actual series number is
        # stored in group(4). 
        if m.group(2) is None:
            series = 0
        else:
            series = int(m.group(4))

        # Make sure to process only the relevant series
        if series != self._seriesNum:
            return []

        # The time index is also not always specified.
        if m.group(5) is None:
            timepoint = 0
        else:
            timepoint = int(m.group(6))

        # Plane number is always specified
        plane = int(m.group(7))

        # Channel number is always specified
        ch = int(m.group(8))

        # Build the channel code
        channelCode = "SERIES-" + str(series) + "_CHANNEL-" + str(ch)

        if self._DEBUG:
            msg = "Current file = " + imagePath + " has series = " + \
            str(series) + " timepoint = " + str(timepoint) + " plane = " + \
            str(plane) + " channel = " + str(ch) + "; channelCode = " + \
            str(channelCode) 
            self._logger.info(msg)

        # Initialize Metadata array
        Metadata = []

        # Initialize a new ImageMetadata object
        imageMetadata = ImageMetadata();

        # Fill in all information
        imageMetadata.imageIdentifier = imageIdentifiers.get(0) 
        imageMetadata.seriesNumber = series
        imageMetadata.timepoint = timepoint
        imageMetadata.depth = plane
        imageMetadata.channelCode = channelCode
        imageMetadata.tileNumber = 1  # + self._seriesNum
        imageMetadata.well = "IGNORED"

        # Now return the image metadata object in an array
        Metadata.append(imageMetadata)
        return Metadata


    def _getChannelName(self, seriesIndx, channelIndx):
        """Returns the channel name (from the parsed metadata) for
        a given channel in a given series."
        """

        # TODO: Get the real channel name from the metadata!

        # Build name of the channel from series and channel indices
        name = "SERIES_" + str(seriesIndx) + "_CHANNEL_" + str(channelIndx)

        return name


    def _getChannelColor(self, seriesIndx, channelIndx):
        """Returns the channel color (from the parsed metadata) for
        a given channel in a given series."
        """

        if self._DEBUG:
            self._logger.info("Trying to find seriesIndx = " + \
                               str(seriesIndx) + " in seriesIndices = " + \
                               str(self._seriesIndices))

        # Get the position in the seriesIndices list
        indx = self._seriesIndices.index(int(seriesIndx))

        # Get the metadata for the requested series
        metadata = self._allSeriesMetadata[indx]

        # Get the metadata
        key = "channelColor" + str(channelIndx)
        color = metadata[key]

        if color is not None:
            color = color.split(",")
            R = int(255 * float(color[0]))
            G = int(255 * float(color[1]))
            B = int(255 * float(color[2]))
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
                R = random.random_integers(0, 255)
                G = random.random_integers(0, 255)
                B = random.random_integers(0, 255)

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

        # Get the indices of series and channel from the channel code
        p = re.compile("SERIES-(\d+)_CHANNEL-(\d+)")
        m = p.match(channelCode)
        if m is None or len(m.groups()) != 2:
            err = "MICROSCOPYCOMPOSITEDATASETCONFIG::_getSeriesAndChannelNumbers(): " + \
            "Could not extract series and channel number!"
            self._logger.error(err)
            raise Exception(err)

        # Now assign the indices
        seriesIndx = int(m.group(1))
        channelIndx = int(m.group(2))

        if self._DEBUG:
            self._logger.info("Current channel code " + channelCode + \
                              "corresponds to series = " + str(seriesIndx) + \
                              " and channel = " + str(channelIndx))

        # Return them
        return seriesIndx, channelIndx
