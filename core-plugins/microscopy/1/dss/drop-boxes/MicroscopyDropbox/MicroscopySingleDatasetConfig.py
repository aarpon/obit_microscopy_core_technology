# -*- coding: utf-8 -*-

"""
Created on Feb 20, 2014

@author: Aaron Ponti
"""

import re
from ch.systemsx.cisd.openbis.dss.etl.dto.api import SimpleImageDataConfig
from ch.systemsx.cisd.openbis.dss.etl.dto.api import SimpleImageContainerDataConfig
from ch.systemsx.cisd.openbis.dss.etl.dto.api.impl import MaximumIntensityProjectionGenerationAlgorithm
from ch.systemsx.cisd.openbis.dss.etl.dto.api import ChannelColor
from ch.systemsx.cisd.openbis.dss.etl.dto.api import ImageIdentifier
from ch.systemsx.cisd.openbis.dss.etl.dto.api import ImageMetadata
from ch.systemsx.cisd.openbis.dss.etl.dto.api import OriginalDataStorageFormat
from ch.systemsx.cisd.openbis.dss.etl.dto.api import ChannelColorRGB
from ch.systemsx.cisd.openbis.dss.etl.dto.api import Channel
import xml.etree.ElementTree as ET

class MicroscopySingleDatasetConfig(SimpleImageContainerDataConfig):
    """Image data configuration class for single image files (with
    optional multiple series)."""

    _DEBUG = False

    # List of metadata attributes obtained either from the settings XML 
    # file generated by the Annotation Tool or returned by 
    # BioFormatsProcessor.getMetadata(asXML=False) 
    # (for all series in the file, sorted by series).
    _allSeriesMetadata = None

    # Number of the series to register (for a multi-series dataset).
    _seriesNum = 0

    # Logger
    _logger = None

    def __init__(self, allSeriesMetadata, logger, seriesNum=0):
        """Constructor.

        @param allSeriesMetadata: list of metadata attributes generated either
                                  by the Annotation Tool and parsed from the
                                  settings XML file, or from BioFormatsProcessor
                                  and returned via:
                                  BioFormatsProcessor.getMetadataXML(asXML=False)
        @param seriesNum:         Int Number of the series to register. All
                                  other series in the file will be ignored.
                                  Set to -1 to register all series to the 
                                  same dataset.
        @param logger:            logger object
        """

        # Store the logger
        self._logger = logger

        # Store the series metadata
        self._allSeriesMetadata = allSeriesMetadata

        # Store the series number
        self._seriesNum = seriesNum

        # This is microscopy data
        self.setMicroscopyData(True)

        # Store raw data in original form
        self.setOriginalDataStorageFormat(OriginalDataStorageFormat.UNCHANGED)

        # Set the image library
        self.setImageLibrary("BioFormats")

        # Disable thumbnail generation by ImageMagick
        self.setUseImageMagicToGenerateThumbnails(False)

        # Enable thumbnail generation for the first series of a file.
        if seriesNum == 0:
            self.setGenerateThumbnails(True)
        else:
            self.setGenerateThumbnails(False)

        # Specify thumbnail resolution explicitly
        resolutions = ['256x256']
        self.setGenerateImageRepresentationsUsingImageResolutions(resolutions)

        # Set the recognized extensions to match those in the Annotation Tool
        self.setRecognizedImageExtensions([\
                "czi", "dv", "ics", "ids", "ims", "lei", "lif",
                "liff", "lsm", "nd", "nd2", "oib", "oif", "ome",
                "r3d", "stk", "tif", "tiff", "zvi"])

        # Set the dataset type
        self.setDataSetType("MICROSCOPY_IMG")

        # Set representative image algorithm
        self.setImageGenerationAlgorithm(MaximumIntensityProjectionGenerationAlgorithm(
                                        "MICROSCOPY_IMG_THUMBNAIL", 256, 256,
                                        "thumbnail.png"))


    def createChannel(self, channelCode):
        """Create a channel from the channelCode with the name as read from
        the file via the MetadataReader and the color (RGB) as read.
    
        @param channelCode Code of the channel as generated by extractImagesMetadata().
        """

        # Get the indices of series and channel from the channel code
        (seriesIndx, channelIndx) = self._getSeriesAndChannelNumbers(channelCode)

        if self._seriesNum != -1 and seriesIndx != self._seriesNum:
            return

        # Get the channel name
        name = self._getChannelName(seriesIndx, channelIndx)
        
        # Get the channel color (RGB)
        colorRGB = self._getChannelColor(seriesIndx, channelIndx)

        # Log
        if self._DEBUG:
            self._logger.info("MICROSCOPYSINGLEDATASETCONFIG::createChannel(): " +
                              "channel (s = " + str(seriesIndx) + ", c = " + 
                              str(channelIndx) + ") has code " + channelCode + 
                              ", color (" + str(colorRGB) + " and name " + name)

        # Return the channel with given name and color (the code is set to
        # be the same as the channel name).
        return Channel(channelCode, name, colorRGB)


    def extractImagesMetadata(self, imagePath, imageIdentifiers):
        """Overrides extractImagesMetadata method making sure to store
        both series and channel indices in the channel code to be reused
        later to extract color information and other metadata.

        The channel code is in the form SERIES-(\d+)_CHANNEL-(\d+).

        Only metadata for the relevant series number is returned!

        @param imagePath Full path to the file to process
        @param imageIdentifiers Array of ImageIdentifier's

        @see constructor.
        """

        # Initialize array of metadata entries
        metaData = []

        # Iterate over all image identifiers
        for id in imageIdentifiers:

            # Extract the info from the image identifier
            ch = int(id.colorChannelIndex)
            plane = int(id.focalPlaneIndex)
            series = int(id.seriesIndex)
            timepoint = int(id.timeSeriesIndex)

            # Make sure to process only the relevant series
            if self._seriesNum != -1 and series != self._seriesNum:
                continue

            # Build the channel code
            channelCode = "SERIES-" + str(series) + "_CHANNEL-" + str(ch)

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

            # Log image geometry information
        if self._DEBUG:
            self._logger.info("MICROSCOPYSINGLEDATASETCONFIG::extractImagesMetadata(): " +
                              "Current image: series = " + str(series) + 
                              " channel = " + str(ch) + 
                              " plane = " + str(plane) + 
                              " timepoint = " + str(timepoint) + 
                              " channel code = " + str(channelCode))

        # Now return the metaData array
        return metaData


    def _getChannelName(self, seriesIndx, channelIndx):
        """Returns the channel name (from the parsed metadata) for
        a given channel in a given series."
        """

        # Get the metadata for the requested series
        metadata = self._allSeriesMetadata[seriesIndx]

        # Try extracting the name for the given series and channel
        try:
            key = "channelName" + str(channelIndx)
            name = metadata[key]

        except KeyError:
            err = "MICROSCOPYSINGLEDATASETCONFIG::createChannel(): " + \
            "Could not create channel name for channel " + str(channelIndx) + \
            " and series " + str(seriesIndx) + "for key = " + \
            key + "  from metadata = " + \
            str(metadata)
            self._logger.error(err)
            raise(err)

        # In case no name was found, assign default name
        if name == "":
            name = "No name"

        return name


    def _getChannelColor(self, seriesIndx, channelIndx):
        """Returns the channel color (from the parsed metadata) for
        a given channel in a given series."
        """

        # Get the metadata for the requested series
        metadata = self._allSeriesMetadata[seriesIndx]

        # Try extracting the color for the given series and channel
        try:
            color = metadata["channelColor" + str(channelIndx)]

        except KeyError:
            err = "MICROSCOPYSINGLEDATASETCONFIG::createChannel(): " + \
            "Could not extract channel color for channel " + \
             str(channelIndex) + " and series " + str(seriesIndx) + \
            " from metadata."
            self._logger.error(err)
            raise(err)

        # Try extracting the color for current channel
        colorComponents = color.split(",")
        assert(len(colorComponents) == 4)
        try:
            R = int(float(colorComponents[0]))
            G = int(float(colorComponents[1]))
            B = int(float(colorComponents[2]))
        except:
            err = "MICROSCOPYSINGLEDATASETCONFIG::createChannel(): " + \
            "Could not extract color with index " + str(channelIndx)
            self._logger.error(err)
            raise(err)

        # Create the ChannelColorRGB object
        colorRGB = ChannelColorRGB(R, G, B)

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
            err = "MICROSCOPYSINGLEDATASETCONFIG::_getSeriesAndChannelNumbers(): " + \
            "Could not extract series and channel number!"
            self._logger.error(err)
            raise Exception(err)

        # Now assign the indices
        seriesIndx = int(m.group(1))
        channelIndx = int(m.group(2))

        # Return them
        return seriesIndx, channelIndx
