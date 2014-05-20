"""
Created on Feb 6, 2014

@author: Aaron Ponti
"""

from loci.formats import FormatTools
from loci.formats import ChannelSeparator
from loci.formats import ChannelFiller
from loci.formats import MetadataTools
from xml.etree import ElementTree as ET

class BioFormatsProcessor:
    """The BioFormatsProcessor class scans a file using the bio-formats library and
    extracts relevant metadata information for registration."""

    # File path
    _filePath = None

    # LOCI reader object
    _reader = None

    # OME metadata store object
    _metadataStore = None

    # Number of series in the file
    _numSeries = 0

    # Metadata dictionary of dictionaries (one per series)
    _metadata = dict()


    def __init__(self, filePath, logger):
        """
        Constructor.
        """

        # Logger
        self._logger = logger

        # Microscopy file path
        self._filePath = filePath

        # Initialize the LOCI reader
        self._reader = ChannelSeparator(ChannelFiller())
        self._reader.setMetadataStore(MetadataTools.createOMEXMLMetadata())

        # Set the filename
        self._reader.setId(self._filePath)

        # Store a reference to the OME metadata store
        self._metadataStore = self._reader.getMetadataStore()


    def parse(self):
        """Scan the metadata for metadata information and stores it."""
        
        # Get the number of series
        self._numSeries = self._reader.getSeriesCount()
        
        for i in range(self._numSeries):
            
            # Set the series
            self._reader.setSeries(i)
            
            # Initialize metadata dictionary for current series
            seriesAttr = {}
            
            # Series number
            seriesAttr["numSeries"] = str(i)
            
            # Image name
            seriesAttr["name"] = self._metadataStore.getImageName(i)
            
            # Image size
            (sizeX, sizeY, sizeZ, sizeC, sizeT) = self._getDatasetSizes()
            seriesAttr["sizeX"] = str(sizeX)
            seriesAttr["sizeY"] = str(sizeY)
            seriesAttr["sizeZ"] = str(sizeZ)
            seriesAttr["sizeC"] = str(sizeC)
            seriesAttr["sizeT"] = str(sizeT)
            
            # Data type
            seriesAttr["datatype"] = self._getDataType()

            # Is signed
            seriesAttr["isSigned"] = str(FormatTools.isSigned(
                                        self._reader.getPixelType()))
            
            # Is little endian
            seriesAttr["isLittleEndian"] = str(self._reader.isLittleEndian())

            # Acquisition date
            seriesAttr["acquisitionDate"] = self._getAcquisitionDate(i)

            # Voxel sizes
            (voxelX, voxelY, voxelZ) = self._getVoxelSizes(i)
            seriesAttr["voxelX"] = str(voxelX)
            seriesAttr["voxelY"] = str(voxelY)
            seriesAttr["voxelZ"] = str(voxelZ)
            
            # Channel names
            channelNames = self._getChannelNames(i)
            for c in range(len(channelNames)):
                seriesAttr["channelName" + str(c)] = channelNames[c]

            # Emission wavelengths
            emWavelegths = self._getEmissionWavelengths(i)
            for c in range(len(emWavelegths)):
                seriesAttr["emWavelegth" + str(c)] = str(emWavelegths[c])
            
            # Excitation wavelengths
            exWavelegths = self._getExcitationWavelengths(i)
            for c in range(len(exWavelegths)):
                seriesAttr["exWavelegth" + str(c)] = str(exWavelegths[c])

            # Stage positions
            (stageX, stageY) = self._getStagePosition()
            seriesAttr["positionX"] = str(stageX)
            seriesAttr["positionY"] = str(stageY)

            # Channel colors
            channelColors = self._getChannelColors(i)
            for c in range(len(channelColors)):
                seriesAttr["channelColor" + str(c)] = \
                str(channelColors[c][0]) + ", " + \
                str(channelColors[c][1]) + ", " + \
                str(channelColors[c][2]) + ", " + \
                str(channelColors[c][3])

            # Numerical apertures
            NAs = self._getNAs()
            if NAs is None or len(NAs) == 0:
                seriesAttr["NA"] = str(float("nan"))
            elif len(NAs) == 1:
                seriesAttr["NA"] = NAs[0]
            else:
                seriesAttr["NA"] = ', '.join(NAs)


            # Store metadata for current series
            seriesKey = "series_" + str(i)
            self._metadata[seriesKey] = seriesAttr


    def getMetadata(self):
        """
        Return the extracted metadata.
        """

        return self._metadata


    def getMetadataXML(self):
        """
        Return the extracted metadata in an array of Annotation Tool-
        compatible XML nodes.
        """
        
        xml = []
        for key in self._metadata.keys():
            
            # Create an XML node (the key is "series_n", with n = 0, 1, ...)
            node = ET.Element(key)

            # Get dictionary of metadata attributes for current series
            d = self._metadata[key]
            
            # Add all attributes to the XML node
            for k, v in d.iteritems():
                node.set(k, str(v))

            # Convert node to string and append
            xml.append(ET.tostring(node))

        # Return the array of XML strings
        return xml


    def getNumSeries(self):
        """
        Return the number of series in file.
        """

        return self._numSeries


    # # #
    # # # PRIVATE METHODS
    # # #

    def _getAcquisitionDate(self, n):
        """
        Extract the acquisition dates from all series.
        """

        acqDate = self._metadataStore.getImageAcquisitionDate(n)
        if acqDate is None:
            acqDate = ''
        else:
            acqDate = acqDate.getValue()

        return acqDate


    def _getChannelColors(self, n):
        """
        Extracts the colors as RGBA vectors of all channels from current series.
        """

        # Get the number of channels in this series
        nChannels = self._reader.getSizeC()

        # Initialize channel color array
        channelColors = []
        
        for ch in range(nChannels):

            # Get the channel color
            color = self._metadataStore.getChannelColor(n, ch)
            if color is None:
                colorsRGBA = [255, 255, 255, 255]
            else:
                colorsRGBA = [color.getRed(), color.getGreen(),
                              color.getBlue(), color.getAlpha()]

            # Store color for current channel in current series
            channelColors.append(colorsRGBA)

        return channelColors


    def _getChannelNames(self, n):
        """
        Extracts the names of all channels from all series.
        """

        # Get the number of channels in this series
        nChannels = self._reader.getSizeC()

        # Initialize channel name list
        channelNames = []
        
        for ch in range(nChannels):

            # Get channel name
            name = self._metadataStore.getChannelName(n, ch)
            if name is None:
                name = "No name"

            # Remove 0-byte at the end of the string if present
            if name.endswith('\x00'):
                name = name[:-1]

            # Store name for current channel
            channelNames.append(name)
                                
        return channelNames


    def _getDatasetSizes(self):
        """
        Extract dataset sizes for current series.
        """

        # Get sizes
        sizeX = self._reader.getSizeX();
        sizeY = self._reader.getSizeY();
        sizeZ = self._reader.getSizeZ();
        sizeC = self._reader.getSizeC();
        sizeT = self._reader.getSizeT();

        # Return them
        return (sizeX, sizeY, sizeZ, sizeC, sizeT)


    def _getDataType(self):
        """
        Get data type for current series.
        """

        # Get the pixel type
        pixelType = self._reader.getPixelType()

        # Bytes per pixel
        BytesPerPixel = FormatTools.getBytesPerPixel(pixelType)
        if BytesPerPixel == 1:
            datatype = 'uint8'
        elif BytesPerPixel == 2:
            datatype = 'uint16'
        elif BytesPerPixel == 4:
            # This is 32-bit floating point
            datatype = 'float'
        else:
            datatype = "unsupported"

        return datatype


    def _getNAs(self):
        """
        Get the numerical aperture for current series.
        """

        # Get and store all numerical apertures (shouldn't it be one?)
        numericalApertures = []
        for i in range(self._metadataStore.getInstrumentCount()):
            for o in range(self._metadataStore.getObjectiveCount(i)):
                NA = self._metadataStore.getObjectiveLensNA(i, o)
                if NA is None:
                    NA = float("nan")
                numericalApertures.append(NA)

        return numericalApertures


    def _getStagePosition(self):
        """Extract the stage positions."""
        
        metadata = self._reader.getSeriesMetadata()
        keys = metadata.keySet()
        if keys.contains('X position'):
            m = metadata.get('X position')
            n = Number(m)
            x = n.doubleValue()
        else:
            x = float("nan")

        if keys.contains('Y position'):
            m = metadata.get('Y position')
            n = Number(m)
            y = n.doubleValue()
        else:
            y = float("nan")

        return (x, y)


    def _getTimeStamps(self):
        """
        Extracts the timestamps from current series.
        
        TODO: Currently unused
        """

        # Get and store all channel names
        timestamps = []

        # Number of time stamps to retrieve
        nTimepoints = self._reader.getSizeT()

        # Iterate over the keys and get the values
        for tp in range(nTimepoints):

            option = 'timestamp ' + str(tp)
            t = self._reader.getSeriesMetadataValue(option)
            if t is None:
                t = float("nan")

            # Store timestamps for current series
            timestamps.append(t)

        return timestamps


    def _getVoxelSizes(self, n):
        """
        Extract voxel sizes for current series.
        """

        # Voxel size X
        voxelX = self._metadataStore.getPixelsPhysicalSizeX(n)
        if voxelX is None:
            voxelX = float("nan")
        else:
            voxelX = voxelX.getValue()

        # Voxel size Y
        voxelY = self._metadataStore.getPixelsPhysicalSizeY(n)
        if voxelY is None:
            if voxelX is None:
                voxelY = float("nan")
            else:
                # Some formats store just one size for X and Y,
                # if they are equal
                voxelY = voxelX
        else:
            voxelY = voxelY.getValue()

        # Voxel size Z
        voxelZ = self._metadataStore.getPixelsPhysicalSizeZ(n)
        if voxelZ is None:
            voxelZ = float("nan");
        else:
            voxelZ = voxelZ.getValue()

        return (voxelX, voxelY, voxelZ)


    def _getEmissionWavelengths(self, n):
        """
        Extracts the excitation and emission wavelengths of all channels
        from current series.
        """

        # Get the number of channels in this series
        nChannels = self._reader.getSizeC()

        # Initialize array
        emWavelengths = []

        for ch in range(nChannels):

            # Get and store emission wavelength for current channel in
            # current series
            em = self._metadataStore.getChannelEmissionWavelength(n, ch)
            if em is None:
                em = float("nan")
            emWavelengths.append(em)

        return emWavelengths


    def _getExcitationWavelengths(self, n):
        """
        Extracts the excitation and emission wavelengths of all channels
        from current series.
        """

        # Get the number of channels in this series
        nChannels = self._reader.getSizeC()

        # Initialize array
        exWavelengths = []

        for ch in range(nChannels):

            # Get and store excitation wavelength for current channel in
            # current series
            ex = self._metadataStore.getChannelExcitationWavelength(n, ch)
            if ex is None:
                ex = float("nan")
            exWavelengths.append(ex)
        
        return exWavelengths


    def _markThumbnails(self):
        """
        Mark which series contain thumbnails.
        """

        # Mark all series whether they are thumbnails or not
        for n in range(self._nSeries):

            # Change to current series
            self._reader.setSeries(n)

            # Check if thumbnail
            self._metadata[n]['isThumbnail'] = self._reader.isThumbnailSeries()
