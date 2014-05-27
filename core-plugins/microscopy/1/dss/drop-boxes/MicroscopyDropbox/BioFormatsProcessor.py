"""
Created on Feb 6, 2014

@author: Aaron Ponti
"""

from loci.formats import FormatTools
from loci.formats import ChannelSeparator
from loci.formats import ChannelFiller
from loci.formats import MetadataTools
from xml.etree import ElementTree as ET
import ch.ethz.scu.obit.microscopy.readers.MicroscopyReader as MicroscopyReader
import java.io.File
import java.util.Arrays

class BioFormatsProcessor:
    """The BioFormatsProcessor class scans a file using the bio-formats library and
    extracts relevant metadata information for registration."""

    # MicroscopyReader (Java) object
    _microscopyReader = None


    def __init__(self, filePath, logger):
        """
        Constructor.
        """

        # Logger
        self._logger = logger

        # Initialize the MicroscopyReader
        self._microscopyReader = MicroscopyReader(java.io.File(filePath))


    def bioformats_version(self):
        """Return the version of the bio-formats library used for parsing the
        metadata information."""

        return str(self._microscopyReader.bioformatsVersion())


    def parse(self):
        """Scan the metadata for metadata information and stores it."""
        
        self._microscopyReader.parse()


    def getMetadata(self, asXML=False):
        """
        Return the series metadata in a list.
        """

        # Get the metadata from the MicroscopyReader
        metadata = self._microscopyReader.getAttributes()

        # Instantiate metadata list
        seriesMetadataArray = []

        # Important: make sure to return metadata sorted by series number!
        keys = metadata.keySet().toArray()
        java.util.Arrays.sort(keys)
        
        # Process all series
        for key in keys:

            # Create an XML node
            node = ET.Element("MicroscopyFileSeries")

            # Get metadata attributes for current series
            d = metadata.get(key)

            # Add all attributes to the XML node (make sure to encode 
            # everything as unicode).
            metadataKeys = d.keySet()
            for metadataKey in metadataKeys:
                key = metadataKey.encode('utf-8')
                value = (d.get(metadataKey)).encode('utf-8')
                node.set(key, value)

            # Convert to XML string if needed or append as is
            if asXML is True:
                seriesMetadataArray.append(ET.tostring(node))
            else:
                seriesMetadataArray.append(node.attrib)

        # Return the list of metadata entries per series
        return seriesMetadataArray


    def getNumSeries(self):
        """
        Return the number of series in file.
        """

        return self._microscopyReader.getNumberOfSeries()
