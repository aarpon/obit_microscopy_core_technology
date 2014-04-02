"""
Created on Feb 6, 2014

@author: Aaron Ponti
"""

from loci.formats import FormatTools
from loci.formats import ChannelSeparator
from loci.formats import ChannelFiller
from loci.formats import MetadataTools

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
    _nSeries = 0

    # Array of metadata disctionaries (one per series)
    _metadata = []


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

        # Initialize the metadata structure
        self._initMetadata()


    def extractMetadata(self):
        """Extract and store needed metadata"""

        # Dataset sizes
        self._getDatasetSizes()

        # Data types
        self._getDataTypes()

        # Voxel sizes
        self._getVoxelSizes()

        # Acquisition dates
        self._getAcquisitionDates()

        # Mark thumbnails
        self._markThumbnails()

        # Channel names
        self._getChannelNames()

        # Channel colors
        self._getChannelColors()

        # Get wavelengths
        self._getWavelengths()

        # Get time stamps
        self._getTimeStamps()


    def getMetadata(self):
        """
        Return the extracted metadata.
        """

        return self._metadata


    def getNumSeries(self):
        """
        Return the number of series in file.
        """

        return self._nSeries


    # # #
    # # # PRIVATE METHODS
    # # #

    def _initMetadata(self):

        # Initialize metadata dictionary
        metadata = {'seriesNumber'      : 0,
                    'nImages'           : 0,
                    'sizeX'             : 0,
                    'sizeY'             : 0,
                    'sizeZ'             : 0,
                    'sizeC'             : 0,
                    'sizeT'             : 0,
                    'voxelSizeX'        : 0,
                    'voxelSizeY'        : 0,
                    'voxelSizeZ'        : 0,
                    'datatype'          : None,
                    'isLittleEndian'    : False,
                    'isSigned'          : False,
                    'isThumbnail'       : False,
                    'acquisitionDate'   : '',
                    'channelNames'      : [],
                    'channelColors'     : [],
                    'emWavelengths'     : [],
                    'exWavelengths'     : [],
                    'NumericalAperture' : 0,
                    'timestamps'        : []}

        # Get and store the number of series
        self._nSeries = self._reader.getSeriesCount()

        # Initialize metadata dictionaries (one per series)
        n = 0
        while n < self._nSeries:
            self._metadata.append(metadata.copy())
            n += 1


    def _getAcquisitionDates(self):
        """
        Extract the acquisition dates from all series.
        """

        # Get and store all acquisition dates
        for n in range(self._nSeries):

            # Change to current series
            self._reader.setSeries(n)

            acqDate = self._metadataStore.getImageAcquisitionDate(n)
            if acqDate is None:
                acqDate = ''
            else:
                acqDate = acqDate.getValue()

            self._metadata[n]['acquisitionDate'] = acqDate


    def _getChannelColors(self):
        """
        Extracts the colors as RGBA vectors of all channels from all series.
        """

        # Get and store all channel names
        for n in range(self._nSeries):

            # Initialize
            self._metadata[n]['channelColors'] = []

            # Change to series
            self._reader.setSeries(n)

            # Get the number of channels in this series
            nChannels = self._reader.getSizeC()

            for ch in range(nChannels):

                # Get the channel color
                color = self._metadataStore.getChannelColor(n, ch)
                if color is None:
                    colorsRGBA = [255, 255, 255, 255]
                else:
                    colorsRGBA = [color.getRed(), color.getGreen(),
                                  color.getBlue(), color.getAlpha()]

                # Store color for current channel in current series
                self._metadata[n]['channelColors'].append(colorsRGBA)


    def _getChannelNames(self):
        """
        Extracts the names of all channels from all series.
        """

        # Get and store all channel names
        for n in range(self._nSeries):

            # Initialize
            self._metadata[n]['channelNames'] = []

            # Change to series
            self._reader.setSeries(n)

            # Get the number of channels in this series
            nChannels = self._reader.getSizeC()

            for ch in range(nChannels):

                # Get channel name
                name = self._metadataStore.getChannelName(n, ch)
                if name is None:
                    name = "No name"

                # Remove 0-byte at the end of the string if present
                if name.endswith('\x00'):
                    name = name[:-1]

                # Store name for current channel in current series
                self._metadata[n]['channelNames'].append(name)


    def _getDatasetSizes(self):
        """
        Extract dataset sizes for all series.
        """

        # Get and store all dataset sizes for all series
        for n in range(self._nSeries):

            # Change to current series
            self._reader.setSeries(n)

            # Get sizes
            self._metadata[n]['nImages'] = self._reader.getImageCount();
            self._metadata[n]['sizeX'] = self._reader.getSizeX();
            self._metadata[n]['sizeY'] = self._reader.getSizeY();
            self._metadata[n]['sizeZ'] = self._reader.getSizeZ();
            self._metadata[n]['sizeC'] = self._reader.getSizeC();
            self._metadata[n]['sizeT'] = self._reader.getSizeT();


    def _getDataTypes(self):
        """
        Get data types for all series.
        """

        # Get and store all dataset sizes for all series
        for n in range(self._nSeries):

            # Change to current series
            self._reader.setSeries(n)

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
                datatype = 'single'
            else:
                datatype = "unsupported"

            # Is the data type signed?
            isSigned = FormatTools.isSigned(pixelType)

            # Endianity
            isLittleEndian = self._reader.isLittleEndian()

            # Store data type information
            self._metadata[n]['datatype'] = datatype
            self._metadata[n]['isLittleEndian'] = isLittleEndian
            self._metadata[n]['isSigned'] = isSigned


    def _getNAs(self):
        """
        Get the numerical aperture for all series.
        """

        # Get and store all numerical apertures
        for n in range(self._nSeries):

            # Initialize
            self._metadata[n]['NumericalAperture'] = []

            # Change to series
            self._reader.setSeries(n)

            # Get the number of instruments and objectives for this series
            # Expected: 1 and 1.
            nInstr = self._metadataStore.getInstrumentCount()
            nObj = self._metadataStore.getObjectiveCount()

            for i in range(nInstr):
                for o in range(nObj):
                    NA = self._metadataStore.getObjectiveLensNA(i, o)
                    self._metadata[n]['NumericalAperture'].append(NA)


    def _getTimeStamps(self):
        """
        Extracts the timestamps from all series.
        """

        # Get and store all channel names
        for n in range(self._nSeries):

            # Initialize
            self._metadata[n]['timestamps'] = []

            # Change to series
            self._reader.setSeries(n)

            # Number of time stamps to retrieve
            nTimepoints = self._reader.getSizeT()

            # Iterate over the keys and get the values
            for tp in range(nTimepoints):

                option = 'timestamp ' + str(tp)
                t = self._reader.getSeriesMetadataValue(option)
                if t is None:
                    t = "NaN"

                # Store timestamps for current series
                self._metadata[n]['timestamps'].append(t)


    def _getVoxelSizes(self):
        """
        Extract voxel sizes for all series.
        """

        # Get and store all voxel sizes for all series
        for n in range(self._nSeries):

            # Change to current series
            self._reader.setSeries(n)

            # Voxel size X
            voxelX = self._metadataStore.getPixelsPhysicalSizeX(n)
            if voxelX is None:
                voxelX = 0;
            else:
                voxelX = voxelX.getValue()

            self._metadata[n]['voxelSizeX'] = voxelX

            # Voxel size Y
            voxelY = self._metadataStore.getPixelsPhysicalSizeY(n)
            if voxelY is None:
                voxelY = 0;
            else:
                voxelY = voxelY.getValue()

            self._metadata[n]['voxelSizeY'] = voxelY

            # Voxel size Z
            voxelZ = self._metadataStore.getPixelsPhysicalSizeZ(n)
            if voxelZ is None:
                voxelZ = 0;
            else:
                voxelZ = voxelZ.getValue()

            self._metadata[n]['voxelSizeZ'] = voxelZ


    def _getWavelengths(self):
        """
        Extracts the excitation and emission wavelengths of all channels
        from all series.
        """

        # Get and store all channel names
        for n in range(self._nSeries):

            # Initialize
            self._metadata[n]['exWavelengths'] = []
            self._metadata[n]['emWavelengths'] = []

            # Change to series
            self._reader.setSeries(n)

            # Get the number of channels in this series
            nChannels = self._reader.getSizeC()

            for ch in range(nChannels):

                # Get and store emission wavelength for current channel in
                # current series
                em = self._metadataStore.getChannelEmissionWavelength(n, ch)
                if em is None:
                    em = "NaN"
                self._metadata[n]['emWavelengths'].append(em)

                # Get and store excitation wavelength for current channel in
                # current series
                ex = self._metadataStore.getChannelExcitationWavelength(n, ch)
                if ex is None:
                    ex = "NaN"
                self._metadata[n]['exWavelengths'].append(ex)


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
