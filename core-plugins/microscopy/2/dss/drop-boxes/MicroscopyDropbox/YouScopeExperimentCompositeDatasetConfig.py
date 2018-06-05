# -*- coding: utf-8 -*-

"""
Created on Feb 20, 2014

@author: Aaron Ponti
"""

import re
import random
import math
from os import listdir
from os.path import isfile
from os.path import join
from MicroscopyCompositeDatasetConfig import MicroscopyCompositeDatasetConfig
from YouScopeExperimentMaximumIntensityProjectionGenerationAlgorithm import YouScopeExperimentMaximumIntensityProjectionGenerationAlgorithm
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

class YouScopeExperimentCompositeDatasetConfig(MicroscopyCompositeDatasetConfig):
    """Image data configuration class for YouScope experiments."""

    _DEBUG = False

    # Map of the rows from the images.csv file as processed
    # by YouScopeExperimentCompositeDatasetConfig.buildImagesCSVTable()
    _csvTable = {}

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

    # Keep track of the channel names
    _channelNames = []

    # Logger
    _logger = None

    # Dataset base name
    _basename = ""

    # Metadata folder
    _metadataFolder = ""

    # Maintain a metadata array
    _metadata = []

    # Regular expression patterns  
    _pattern_pos = re.compile(r'(y-tile: (?P<y>\d+)*(, )?)*(x-tile: (?P<x>\d+)*(, )?)*(z-stack: (?P<z>\d+))*',
                              re.IGNORECASE|re.UNICODE)

    _pattern_time_name = re.compile(r'.*_time(?P<time>\d*)\.tif{1,2}$',
                               re.IGNORECASE|re.UNICODE)

    _pattern_time_name_fb = re.compile(r'.*_time_(.*)_\(number_(?P<time>\d*)\)\.tif{1,2}$',
                                  re.IGNORECASE|re.UNICODE)

    _pattern_pos_name = re.compile(r'.*position(?P<pos>\d*)_time.*\.tif{1,2}$',
                                   re.IGNORECASE|re.UNICODE)


    _pattern_pos_name_fb = re.compile(r'.*\(pos_(?P<pos>\d*)\).*$',
                                      re.IGNORECASE|re.UNICODE)

    def __init__(self, csvTable, allSeriesMetadata, seriesIndices, logger, seriesNum=0):
        """Constructor.

        @param csvTable:          map of the rows from the images.csv file as processed
                                  by YouScopeExperimentCompositeDatasetConfig.buildImagesCSVTable()
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

        # Store the csvTable
        self._csvTable = csvTable

        # Store all channel names in the dataset
        for key in self._csvTable:
            row = self._csvTable[key]
            channelName = self._buildChannelName(row)
            if channelName not in self._channelNames:
                self._channelNames.append(channelName) 

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
            raise(Exception("seriesNum (" + str(self._seriesNum) + ") MUST be contained " + \
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

        # Set the recognized extensions -- currently just tif(f)
        self.setRecognizedImageExtensions(["tif", "tiff"])

        # Set the dataset type
        self.setDataSetType("MICROSCOPY_IMG")

        # Create representative image (MIP) for the first series only
        if self._seriesIndices.index(self._seriesNum) == 0:
            self.setImageGenerationAlgorithm(
                YouScopeExperimentMaximumIntensityProjectionGenerationAlgorithm(
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
            self._logger.info("YOUSCOPEEXPERIMENTCOMPOSITEDATASETCONFIG::createChannel(): " + 
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
        self._logger.info("Processing file " + str(imagePath) + " with identifiers " + str(imageIdentifiers))

        # Find the file in the csvTable hashmap
        row = self._csvTable[imagePath]
        self._logger.info("File " + imagePath + " was found in the CSV table.")
        self._logger.info("The corresponding row is " + str(row))

        # Initialize
        tileX = -1
        tileY = -1
        planeNum = -1
        timeNum = -1
        well = ""
        id = ""

        # Test position string
        self._logger.info("Position string is " + str(row[5]))

        # First, get position information
        m_pos = self._pattern_pos.match(row[5])
        if m_pos is not None:
            if m_pos.group("x") is not None:
                tileX = int(m_pos.group("x"))
            if m_pos.group("y") is not None:
                tileY = int(m_pos.group("y"))
            if m_pos.group("z") is not None:
                tileZ = int(m_pos.group("z"))

        # Get the well
        well = row[4]

        # If the positional information could not be extracted from the corresponding
        # column, try to get it from the file name
        m_pos_name = self._pattern_pos_name.match(row[6])
        if m_pos_name is not None:
            if m_pos_name.group("pos") is not None:
                map = self._processPosFromFileName(m_pos_name.group("pos"))
                if tileX == -1 and map.get("tileX") != "":
                    tileX = int(map.get("tileX"))
                if tileY == -1 and map.get("tileY") != "":
                    tileY = int(map.get("tileY"))
                if planeNum == -1 and map.get("planeNum") != "":
                    planeNum = int(map.get("planeNum"))
                if well == "" and map.get("well") != "":
                    well = map.get("well")
        else:
            # Try the fallback option
            m_pos_name_fb = self._pattern_pos_name_fb.match(row[6])
            if m_pos_name_fb is not None:
                if m_pos_name_fb.group("pos") is not None:
                    map = self._processPosFromFileName(m_pos_name_fb.group("pos"))
                    if tileX == -1 and map.get("tileX") != "":
                        tileX = int(map.get("tileX"))
                    if tileY == -1 and map.get("tileY") != "":
                        tileY = int(map.get("tileY"))
                    if planeNum == -1 and map.get("planeNum") != "":
                        planeNum = int(map.get("planeNum"))
                    if well == "" and map.get("well") != "":
                        well = map.get("well")

        # Then, get time information
        m_time = self._pattern_time_name.match(row[6])
        if m_time is not None:
            if m_time.group("time") is not None:
                timeNum = int(m_time.group("time"))
        else:
            # Try the fallback option
            m_time_fb = self._pattern_time_name_fb.match(row[6])
            if m_time_fb is not None:
                if m_time_fb.group("time") is not None:
                    timeNum = int(m_time_fb.group("time"))

        # Fallback
        if tileX == -1:
            tileX = 1
        if tileY == -1:
            tileY = 1
        if planeNum == -1:
            planeNum = 1
        if timeNum == -1:
            timeNum = 1

        # Channel name
        channelName = self._buildChannelName(row)

        # Build series ID from row (if present, use path information to build a unique id)
        seriesID = "Well_" + well + "_Pos_" + str(tileX) + "_" + str(tileY) + "_Path_" + \
            self._pathInfoAsID(row[6])

        # Find the series number that correspond to seriesID
        series = self._seriesNumFromSeriesID(seriesID)

        # Inform
        if series == -1:
            err = "Series with ID " + seriesID + " could not be found!"
            self._logger.error(err)
            raise(Exception(err))
        else:
            self._logger.info("Series with ID " + seriesID + " corresponds to series number " + str(series))

        # Make sure to process only the relevant series
        if series != self._seriesNum:
            return []

        # Get channel index from channel name
        channel = self._getChannelNumber(self._allSeriesMetadata[series], channelName) 

        # Build the channel code
        channelCode = "SERIES-" + str(series) + "_CHANNEL-" + str(channel)

        if self._DEBUG:
            msg = "Current file = " + imagePath + " has series = " + \
            str(series) + " timepoint = " + str(timeNum) + " plane = " + \
            str(planeNum) + " channel = " + str(channel) + " channelCode = " + \
            str(channelCode) 
            self._logger.info(msg)

        # Initialize Metadata array
        Metadata = []

        # Initialize a new ImageMetadata object
        imageMetadata = ImageMetadata()

        # Build a tile number from tileX and tileY
        tileNum = 1000 * tileX + tileY
        if tileNum < 1:
            tileNum = 1
        self._logger.info("Tile number is " + str(tileNum))

        # Fill in all information
        imageMetadata.imageIdentifier = imageIdentifiers.get(0) 
        imageMetadata.seriesNumber = series
        imageMetadata.timepoint = timeNum
        imageMetadata.depth = planeNum
        imageMetadata.channelCode = channelCode
        imageMetadata.tileNumber = tileNum
        imageMetadata.well = well

        # Now return the image metadata object in an array
        Metadata.append(imageMetadata)
        return Metadata


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
            err = "YOUSCOPEEXPERIMENTCOMPOSITEDATASETCONFIG::getChannelName(): " + \
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
            color = color.split(",")
            R = int(255 * float(color[0]))
            G = int(255 * float(color[1]))
            B = int(255 * float(color[2]))
        else:

            # If there is only one channel in the whole dataset,
            # we make it gray value
            if len(self._channelNames) == 1:
                # Fall back to gray
                R = 255
                G = 255
                B = 255
            else:
                # Fall back to default colors    
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
                elif channelIndx == 3:
                    R = 255
                    G = 255
                    B = 0
                elif channelIndx == 4:
                    R = 255
                    G = 0
                    B = 255
                elif channelIndx == 5:
                    R = 0
                    G = 255
                    B = 255
                elif channelIndx == 7:
                    R = 255
                    G = 255
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


    def _getChannelNumber(self, metadata, name):
        """
        Return the channel number from metadata and channel name.
        """
        self._logger.info("Searching for channel '" + name + "' in metadata.")
        for attr_name in metadata:
            if attr_name.startswith("channelName"):
                if metadata[attr_name] == name:
                    channelNumber = int(attr_name[11:])
                    self._logger.info("Found channel number " + str(channelNumber))
                    return channelNumber
        raise Exception("Found no channel with name " + name)


    def _pathInfoAsID(self, filename):

        # Initialize output
        pathInfo = ""

        # We work with a relative path
        filename = filename.replace("\\\\", "\\")
        filename = filename.replace("\\", "/")
        pos = filename.rfind("/")
        if pos != -1:
            pathInfo = filename[0:pos]
            pathInfo = pathInfo.replace("/", "_")
        else:
            pathInfo = "."

        return pathInfo

    def _seriesNumFromSeriesID(self, seriesId):
        """
        Return the series number from its unique ID.
        """

        for i in range(len(self._allSeriesMetadata)):
            metadata = self._allSeriesMetadata[i]
            if metadata['uniqueSeriesID'] == seriesId:
                return i

        return -1


    @staticmethod
    def buildImagesCSVTable(fileName, logger):

        # Initialize the table
        csvTable = HashMap()

        # Header
        isHeader = True

        # Read the CSV file
        br = BufferedReader(FileReader(fileName))

        # Read the first line from the text file
        line = br.readLine()

        # loop until all lines are read 
        while line is not None:

            if isHeader:

                # We are past the header
                isHeader = False

                # Read next line 
                line = br.readLine()

                continue

            # Get all values for current row
            row = line.split(";")

            # Remove '"' and '\' characters if needed
            for i in range(len(row)):
                row[i] = row[i].replace("\"", "")
                row[i] = row[i].replace("\\\\", "\\")
                row[i] = row[i].replace("\\", "/")

            # Add the row with the file name as key
            csvTable.put(row[6], row)

            # Read next line 
            line = br.readLine()

        return csvTable


    @staticmethod
    def registerAccessoryFilesAsDatasets(fullpath, relativePath, transaction,
                                         openBISExperiment, sample, parent_dataset,
                                         logger):
        """Scan the given path for files at the root levels that are
        not images files {.tif|.tiff} and associates them to the
        sample that maps to the composite dataset in the given
        openBISExperiment as MICROSCOPY_ACCESSORY_FILEs."""

        # Extract the path relative to the experiment folder
        if relativePath.endswith('/'):
            relativePath = relativePath[0:len(relativePath) - 1]

        last_index = relativePath.rfind('/')
        if last_index != -1:
            relativePath = relativePath[last_index + 1:]

        logger.info("Relative path is: " + relativePath)

        # Get the list of files at the root of full path that are not image files
        files = [f for f in listdir(fullpath) if isfile(join(fullpath, f)) and
                 not (f.lower().endswith(".tif") or f.lower().endswith(".tiff"))]

        # Report
        logger.info("Accessory files to process: " + str(files))

        # Register them as datasets
        datasetType = "MICROSCOPY_ACCESSORY_FILE"

        for f in files:

            # Log
            logger.info("Registering accessory file: " + f)

            # Create a new dataset
            dataset = transaction.createNewDataSet()
            if not dataset:
                msg = "Could not get or create dataset"
                logger.error(msg)
                raise Exception(msg)

            # Set the dataset type
            dataset.setDataSetType(datasetType)

            # Set the MICROSCOPY_ACCESSORY_FILE_NAME property
            dataset.setPropertyValue("MICROSCOPY_ACCESSORY_FILE_NAME", f)

            # Assign the dataset to the sample
            dataset.setSample(sample)

            # Assign the dataset to the experiment
            dataset.setExperiment(openBISExperiment)

            # Add to the container dataset
            dataset.setParentDatasets([parent_dataset.getDataSetCode()])

            # Move to a custom destination (to match the image datasets)
            dstPath = join("original", relativePath, f)
            transaction.moveFile(join(fullpath, f), dataset, dstPath)

        return True


    def _processPosFromFileName(self, pos):
        """Process position information from file name."""

        # Initialize positions
        map = HashMap()
        map.put("tileX", "")
        map.put("tileY", "")
        map.put("planeNum", "")
        map.put("well", "")

        if pos == "":
            return map

        # Inform
        self._logger.info("Position string to process: " + pos)

        len_pos = len(pos)

        if len_pos == 4:
            # No well, no tiles, and no Z information (2D acquisition)
            map.put("tileX", str(int(pos[0:2])))
            map.put("tileY", str(int(pos[2:4])))
        elif len_pos == 6 or len_pos == 7:
            # Note: the number of digits that encode the well are
            # hard-coded to 4. They do not have to be; unfortunately,
            # it is not possible to know how to break down the pos
            # string in its components. Usually, the well information
            # is stored in the well column of image.csv, and therefore
            # this information is not used.
            map.put("well", self._wellFromPosition(pos[0:4]))
            map.put("planeNum", int(pos[4:]))
        elif len_pos == 8:
            map.put("well", self._wellFromPosition(pos[0:4]))
            map.put("tileX", str(int(pos[4:6])))
            map.put("tileY", str(int(pos[6:8])))
        elif len_pos == 10 or len_pos == 11:
            map.put("well", self._wellFromPosition(pos[0:4]))
            map.put("tileX", str(int(pos[4:6])))
            map.put("tileY", str(int(pos[6:8])))
            map.put("planeNum", int(pos[8:]) )
        else:
            self._logger.error("Unexpected 'pos' length!")

        return map


    def _wellFromPosition(self, pos):
        """
        Maps a position to a well. The position is a n-digit string,
        such as '0202' that maps to well B2. The number of digits must be even,
        and the function will divide them in two n/2 subsets.

        The row is given by one or more letters, the column by an integer:
        e.g. 2712 maps to AA12.
        """

        # Number of digits
        len_pos = len(pos)
        sub_len = int(len_pos / 2)

        # Extract the 'row' part of the string (the letter)
        row = int(pos[0:sub_len])

        if row == 0:
            return ""

        # Extract the 'column' part of the string
        col = str(int(pos[sub_len:len_pos]))

        if row <= 26:
            R = LETTERS[row - 1]
            return R + col

        # The row part of the well name if a made
        # of multiple letters

        # Number of digits
        n_digits = math.log(row) / math.log(26)

        # Row string
        R = ''

        while n_digits > 0:

            # Step
            step = 26 ** int(n_digits)

            # Right-most letter
            r = row // step

            # Append the letter
            R = R + LETTERS[r - 1]

            # Now go to the next letter
            row = row - step
            n_digits = n_digits - 1

        return R + col


    def _buildChannelName(self, row):

        # Get the ID
        id = row[7]

        # Get the various parts that compose the channel name
        channelName = ""
        if row[9] == "" and row[10] == "":
            channelName = "undefined"
        elif row[9] != "" and row[10] == "":
            channelName = row[9]
        elif row[9] == "" and row[10] != "":
            channelName = row[10]
        else:
            channelName = row[9] + "_" + row[10]
        if id != "":
            channelName = id + "_" + channelName

        return channelName
