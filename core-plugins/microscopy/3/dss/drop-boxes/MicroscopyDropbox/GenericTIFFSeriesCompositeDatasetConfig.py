# -*- coding: utf-8 -*-

"""
Created on Feb 20, 2014

@author: Aaron Ponti
"""

import re
import random
from MicroscopyCompositeDatasetConfig import MicroscopyCompositeDatasetConfig
from GenericTIFFSeriesMaximumIntensityProjectionGenerationAlgorithm import GenericTIFFSeriesMaximumIntensityProjectionGenerationAlgorithm
from ch.systemsx.cisd.openbis.dss.etl.dto.api import ChannelColor
from ch.systemsx.cisd.openbis.dss.etl.dto.api import ImageIdentifier
from ch.systemsx.cisd.openbis.dss.etl.dto.api import ImageMetadata
from ch.systemsx.cisd.openbis.dss.etl.dto.api import OriginalDataStorageFormat
from ch.systemsx.cisd.openbis.dss.etl.dto.api import ChannelColorRGB
from ch.systemsx.cisd.openbis.dss.etl.dto.api import Channel
import xml.etree.ElementTree as ET
from GlobalSettings import GlobalSettings


class GenericTIFFSeriesCompositeDatasetConfig(MicroscopyCompositeDatasetConfig):
    """Image data configuration class for Generic TIFF series."""

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

    # Maintain a metadata array
    _metadata = []

    # Regular expression pattern
    _pattern = re.compile(r'^(?P<basename>.*?)' + \
                          '((_Series|_s)(?P<series>\d.*?))?' + \
                          '(_t(?P<timepoint>\d.*?))?' + \
                          '_z(?P<plane>\d.*?)' + \
                          '_ch(?P<channel>\d.*?)' + \
                          '\.tif{1,2}$', re.IGNORECASE|re.UNICODE)

    _pattern_simple = re.compile(r'^(?P<basename>.*?)(?P<plane>\d+)\.tif{1,2}$',
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

        # Specify resolution of image representations explicitly
        resolutions = GlobalSettings.ImageResolutions
        if not resolutions:
            self._logger.info("Skipping thumbnails generation.")
            self.setGenerateThumbnails(False)
        else:
            self._logger.info("Creating thumbnails at resolutions: " + str(resolutions))
            self.setGenerateImageRepresentationsUsingImageResolutions(resolutions)
            self.setGenerateThumbnails(True)

        # Set the recognized extensions -- currently just tif(f)
        self.setRecognizedImageExtensions(["tif", "tiff"])

        # Set the dataset type
        self.setDataSetType("MICROSCOPY_IMG")

        # Create representative image (MIP) for the first series only
        if self._seriesIndices.index(self._seriesNum) == 0:
            self.setImageGenerationAlgorithm(
                GenericTIFFSeriesMaximumIntensityProjectionGenerationAlgorithm(
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
            self._logger.info("GENERICTIFFSERIESCOMPOSITEDATASETCONFIG::createChannel(): " + 
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
        simple_m = self._pattern_simple.match(imagePath)

        # First we try the more complex regex
        if m is not None:
            
            # Get and store the base name
            basename = m.group("basename")
            if self._basename == "" or self._basename != basename:
                self._basename = basename

            # The series number is not always defined in the file name.
            if m.group("series") is None:
                series = 0
            else:
                series = int(m.group("series"))

            # Make sure to process only the relevant series
            if series != self._seriesNum:
                return []

            # The time index is also not always specified.
            if m.group("timepoint") is None:
                timepoint = 0
            else:
                timepoint = int(m.group("timepoint"))

            # Plane number is always specified
            if m.group("plane") is None:
                plane = 0
            else:
                plane = int(m.group("plane"))
            
            # Channel number is always specified
            if m.group("channel") is None:
                ch = 0
            else:
                ch = int(m.group("channel"))
            
        else:
            
            # Try with the simpler regex
            if simple_m is None:
                err = "MICROSCOPYCOMPOSITEDATASETCONFIG::extractImageMetadata(): " + \
                    "unexpected file name " + str(imagePath)
                self._logger.error(err)
                raise Exception(err)

            # Get and store the base name
            basename = simple_m.group("basename")
            if self._basename == "" or self._basename != basename:
                self._basename = basename

            # Series number
            series = 0
            
            # Make sure to process only the relevant series
            if series != self._seriesNum:
                return []

            # Timepoint
            timepoint = 0

            # Plane number is always specified
            if simple_m.group("plane") is None:
                plane = 0
            else:
                plane = int(simple_m.group("plane"))
            
            # Channel number
            ch = 0
            
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
        imageMetadata = ImageMetadata()

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

        if self._DEBUG:
            self._logger.info("Trying to find channel color for channel " + \
                               str(channelIndx))

        # Get the metadata
        key = "channelColor" + str(channelIndx)
        color = metadata[key]

        if color is not None:
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

        # Work around an issue if all color components are 0
        if R == G == B == 0:
            R = 255
            G = 255
            B = 255
            self._logger.info("Color changed from (0, 0, 0) to (255, 255, 255)")

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
        p = re.compile(r"SERIES-(\d+)_CHANNEL-(\d+)")
        m = p.match(channelCode)
        if m is None or len(m.groups()) != 2:
            err = "GENERICTIFFSERIESCOMPOSITEDATASETCONFIG::_getSeriesAndChannelNumbers(): " + \
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
