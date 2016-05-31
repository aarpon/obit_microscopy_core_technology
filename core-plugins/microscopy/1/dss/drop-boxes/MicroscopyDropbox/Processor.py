# -*- coding: utf-8 -*-

"""
Created on Feb 20, 2014

@author: Aaron Ponti
"""

import java.io.File
from org.apache.commons.io import FileUtils
import logging
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from BioFormatsProcessor import BioFormatsProcessor
from MicroscopySingleDatasetConfig import MicroscopySingleDatasetConfig
from MicroscopyCompositeDatasetConfig import MicroscopyCompositeDatasetConfig
from LeicaTIFFSeriesCompositeDatasetConfig import LeicaTIFFSeriesCompositeDatasetConfig

class Processor:
    """The Processor class performs all steps required for registering datasets
    from the assigned dropbox folder."""

    # A transaction object passed by openBIS
    _transaction = None

    # The incoming folder to process (a java.io.File object)
    _incoming = ""

    # The user name
    _username = ""

    # The logger
    _logger = None

    # Constructor
    def __init__(self, transaction, logger):

        # Store arguments
        self._transaction = transaction
        self._incoming = transaction.getIncoming()
        self._username = ""

        # Set up logging
        self._logger = logger


    def dictToXML(self, d):
        """Converts a dictionary into an XML string."""

        # Create an XML node
        node = ET.Element("MicroscopyFileSeries")

        # Add all attributes to the XML node
        for k, v in d.iteritems():
            node.set(k, v)

        # Convert to XML string
        xml = ET.tostring(node, encoding="UTF-8")

        # Return the XML string
        return xml

    def getCustomTimeStamp(self):
        """Create an univocal time stamp based on the current date and time
        (works around incomplete API of Jython 2.5)."""

        t = datetime.now()
        return t.strftime("%y%d%m%H%M%S") + unicode(t)[20:]

    def getSubFolders(self):
        """Return a list of subfolders of the passed incoming directory.

        @return list of subfolders (String)
        """

        incomingStr = self._incoming.getAbsolutePath()
        return [name for name in os.listdir(incomingStr)
                if os.path.isdir(os.path.join(incomingStr, name))]

    def getOrCreateExperiment(self, expId, expName,
                         expType="MICROSCOPY_EXPERIMENT"):
        """Get the experiment with given ID if it exists, or creates it.

        @param expID, the experiment ID
        @param expName, the experiment name
        @param expType, the experiment type that must already exist; optional,
        default is "MICROSCOPY_EXPERIMENT"
        """

        # Make sure to keep the code length within the limits imposed by
        # openBIS for codes
        if len(expId) > 60:
            expId = expId[0:60]

        # Try getting the experiment
        exp = self._transaction.getExperimentForUpdate(expId)
        if not exp:
            # Log
            msg = "PROCESSOR::getOrCreateExperiment(): " + \
            "The experiment with ID " + expId + " does not exist. Create."
            self._logger.info(msg)

            # Create the experiment
            exp = self._transaction.createNewExperiment(expId, expType)
            if not exp:
                msg = "PROCESSOR::getOrCreateExperiment(): " + \
                "Could not create experiment " + expId + "!"
                self._logger.error(msg)
                raise Exception(msg)
            else:
                self._logger.info("PROCESSOR::getOrCreateExperiment(): " + 
                                  "Created experiment with ID " + expId + ".")
        else:
            # Log
            msg = "PROCESSOR::getOrCreateExperiment(): " + \
            "Registering to already existing experiment with ID " + expId + "."
            self._logger.info(msg)

        # Store the name
        exp.setPropertyValue("MICROSCOPY_EXPERIMENT_NAME", expName)

        return exp

    def createExperiment(self, expId, expName, expType="MICROSCOPY_EXPERIMENT"):
        """Create an experiment with given Experiment ID extended with the addition
        of a string composed from current date and time.

        @param expID, the experiment ID
        @param expName, the experiment name
        @param expType, the experiment type that must already exist; optional,
        default is "MICROSCOPY_EXPERIMENT"
        """

        # Make sure to keep the code length within the limits imposed by
        # openBIS for codes
        if len(expId) > 41:
            expId = expId[0:41]

        # Create univocal ID
        expId = expId + "_" + self.getCustomTimeStamp()

        # Log
        self._logger.info("PROCESSOR::createExperiment(): " + 
                          "Register experiment %s" % expId)

        # Create the experiment
        exp = self._transaction.createNewExperiment(expId, expType)
        if not exp:
            msg = "PROCESSOR::createExperiment(): " + \
            "Could not create experiment " + expId + "!"
            self._logger.error(msg)
            raise Exception(msg)
        else:
            self._logger.info("PROCESSOR::createExperiment(): " + 
                              "Created experiment with ID " + expId + ".")

        # Store the name
        exp.setPropertyValue("MICROSCOPY_EXPERIMENT_NAME", expName)

        return exp

    def processExperiment(self, experimentNode,
                          openBISExpType="MICROSCOPY_EXPERIMENT"):
        """Register an IExperimentUpdatable based on the Experiment XML node.

        @param experimentNode An XML node corresponding to an Experiment
        @param openBISExpType The experiment type
        @return IExperimentUpdatable experiment
        """

        # Get the experiment version
        expVersion = experimentNode.attrib.get("version")
        if expVersion is None:
            expVersion = "0"

        # Get the openBIS identifier
        openBISIdentifier = experimentNode.attrib.get("openBISIdentifier")

        # Get the experiment name
        expName = experimentNode.attrib.get("name")

        # Get the experiment date and reformat it to be compatible
        # with postgreSQL
        # TODO: Add this
        # expDate = self.formatExpDateForPostgreSQL(experimentNode.attrib.get("date"))

        # Get the description
        description = experimentNode.attrib.get("description")

        # Get the acquisition hardware
        # TODO: Add this
        # acqHardware = experimentNode.attrib.get("acq_hardware")

        # Get the acquisition software
        # TODO: Add this
        # acqSoftware = experimentNode.attrib.get("acq_software")

        # Get the owner name
        # TODO: Add this
        # owner = experimentNode.attrib.get("owner_name")

        # Get attachments
        attachments = experimentNode.attrib.get("attachments")

        # Get or create the experiment
        openBISExperiment = self.getOrCreateExperiment(openBISIdentifier,
                                                  expName, openBISExpType)
        if not openBISExperiment:
            msg = "PROCESSOR::processExperiment(): " + \
            "Could not create experiment " + openBISIdentifier
            self._logger.error(msg)
            raise Exception(msg)

        # Get comma-separated tag list
        tagList = experimentNode.attrib.get("tags")
        if tagList != None and tagList != "":

            # Retrieve or create the tags
            openBISTags = self.retrieveOrCreateTags(tagList)

            # Set the metaprojects (tags)
            for openBISTag in openBISTags:
                openBISTag.addEntity(openBISExperiment)

        # Set the date
        # TODO: Add this
        # openBISExperiment.setPropertyValue("MICROSCOPY_EXPERIMENT_DATE",
        #                                   expDate)

        # Set the experiment version
        openBISExperiment.setPropertyValue("MICROSCOPY_EXPERIMENT_VERSION",
                                           expVersion)

        # Set the description -- but only if is not empty. 
        # This makes sure that the description of an already existing experiment
        # is not overridden by an empty string.
        if description != "":
            openBISExperiment.setPropertyValue("MICROSCOPY_EXPERIMENT_DESCRIPTION",
                                               description)
        else:
            currentDescription = openBISExperiment.getPropertyValue("MICROSCOPY_EXPERIMENT_DESCRIPTION")
            if (currentDescription is None or currentDescription == ""):
                openBISExperiment.setPropertyValue("MICROSCOPY_EXPERIMENT_DESCRIPTION", "")

        # TODO: Add this
        # openBISExperiment.setPropertyValue("MICROSCOPY_EXPERIMENT_ACQ_HARDWARE",
        #                                   acqHardware)

        # Set the acquisition hardware friendly name
        openBISExperiment.setPropertyValue("MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME",
                                           self._machinename)
        
        # Set the acquisition software
        # TODO: Add this
        # openBISExperiment.setPropertyValue("MICROSCOPY_EXPERIMENT_ACQ_SOFTWARE",
        #                                   acqSoftware)

        # Set the experiment owner
        # TODO: Add this
        # openBISExperiment.setPropertyValue("MICROSCOPY_EXPERIMENT_OWNER",
        #                                   owner)

        # Add the attachments
        if attachments is not None:

            # Extract all relative file names 
            attachmentFiles = attachments.split(";")

            for f in attachmentFiles:

                # This is an additional security step
                if f == '':
                    continue

                # Inform
                msg = "Adding file attachment " + f 
                self._logger.info(msg)

                # Build the full path
                attachmentFilePath = os.path.join(self._incoming.getAbsolutePath(),
                                                  f)

                # Extract the file name
                attachmentFileName = os.path.basename(attachmentFilePath)

                # Read the attachment into a byte array
                javaFile = java.io.File(attachmentFilePath)
                byteArray = FileUtils.readFileToByteArray(javaFile)

                # Add attachment
                openBISExperiment.addAttachment(attachmentFilePath,
                                                attachmentFileName,
                                                "", byteArray)

        # Return the openBIS Experiment object
        return openBISExperiment

    def processMicroscopyFile(self, microscopyFileNode, openBISExperiment):
        """Register the Microscopy File using the parsed properties file.

        @param microscopyFileNode An XML node corresponding to a microscopy
        file (dataset)
        @param openBISExperiment An ISample object representing an Experiment
        """

        # Assign the file to the dataset (we will use the absolute path)
        relativeFileName = microscopyFileNode.attrib.get("relativeFileName")
        fileName = os.path.join(self._incoming.getAbsolutePath(), relativeFileName)

        # Check if the series metadata has been extracted already (i.e. if
        # the microscopyFileNode has at least one child), otherwise
        # process it
        if len(microscopyFileNode) == 0:
            
            # Instantiate a BioFormatsProcessor
            bioFormatsProcessor = BioFormatsProcessor(fileName, self._logger)

            # Extract series metadata
            bioFormatsProcessor.parse()

            # Get the metadata for the series
            allSeriesMetadata = bioFormatsProcessor.getMetadata()

            # Get the number of series
            num_series = bioFormatsProcessor.getNumSeries()

            # Close the file
            bioFormatsProcessor.close()

        else:

            # Get the metadata for all series from the (processed) settings XML 
            allSeriesMetadata = []
            for series in microscopyFileNode:
                allSeriesMetadata.append(series.attrib)

            # Get the number of series
            num_series = len(microscopyFileNode)

        # Log
        self._logger.info("PROCESSOR::processMicroscopyFile(): " + 
                          "File " + relativeFileName + " contains " + 
                           str(num_series) + " series.")

        # Get the correct space where to create the sample
        identifier = openBISExperiment.getExperimentIdentifier()
        sample_space = identifier[1:identifier.find('/', 1)]
        self._logger.info("Creating sample with auto-generated code in space " + sample_space)

        # Create a sample for the dataset
        sample = self._transaction.createNewSampleWithGeneratedCode(sample_space,
                                                                    "MICROSCOPY_SAMPLE_TYPE")

        # Set the sample name
        sample.setPropertyValue("MICROSCOPY_SAMPLE_NAME",
                                relativeFileName[relativeFileName.rfind('/') + 1:])

        # Set the sample description
        sampleDescr = microscopyFileNode.attrib.get("description")
        if sampleDescr is None:
            sampleDescr = ""
        sample.setPropertyValue("MICROSCOPY_SAMPLE_DESCRIPTION", sampleDescr)

        # Store the sample (file) size in bytes
        datasetSize = microscopyFileNode.attrib.get("datasetSize")
        if datasetSize is not None:
            sample.setPropertyValue("MICROSCOPY_SAMPLE_SIZE_IN_BYTES", datasetSize)

        # Set the experiment
        sample.setExperiment(openBISExperiment)

        # Register all series in the file
        image_data_set = None
        for i in range(num_series):

            # Create a configuration object
            singleDatasetConfig = MicroscopySingleDatasetConfig(allSeriesMetadata,
                                                                self._logger, i)

            # Extract the metadata associated to this series and convert it to
            # XML to store it in the MICROSCOPY_IMG_CONTAINER_METADATA property
            # of the MICROSCOPY_IMG_CONTAINER_METADATA (series) dataset type
            seriesMetadataXML = self.dictToXML(allSeriesMetadata[i])

            # Log the content of the metadata
            self._logger.info("Series metadata (XML): " + str(seriesMetadataXML))

            if image_data_set is None:

                # Register the file for the first time (for series 0)

                # Log
                self._logger.info("PROCESSOR::processMicroscopyFile(): " + 
                                  "Creating new image dataset for file " + 
                                   str(fileName) + " and series 0.")

                # Create an image dataset
                dataset = self._transaction.createNewImageDataSet(singleDatasetConfig,
                                                                  java.io.File(fileName))

                # Store the metadata in the MICROSCOPY_IMG_CONTAINER_METADATA property
                dataset.setPropertyValue("MICROSCOPY_IMG_CONTAINER_METADATA", seriesMetadataXML)

                # Store the series name in the MICROSCOPY_IMG_CONTAINER_NAME property
                dataset.setPropertyValue("MICROSCOPY_IMG_CONTAINER_NAME", allSeriesMetadata[i]["name"])

                # Now store a reference to the first dataset
                image_data_set = dataset

                # Move the file
                self._transaction.moveFile(fileName, image_data_set)

            else:

                # Register subsequent series to point to the same file

                # Log
                self._logger.info("PROCESSOR::processMicroscopyFile(): " + 
                                  "Appending series " + str(i) + " to dataset " +
                                  str(image_data_set))

                # Create an image dataset that points to an existing one
                # (and points to its file)
                dataset = self._transaction.createNewImageDataSetFromDataSet(singleDatasetConfig,
                                                                             image_data_set)

                # Store the metadata in the MICROSCOPY_IMG_CONTAINER_METADATA property
                dataset.setPropertyValue("MICROSCOPY_IMG_CONTAINER_METADATA",
                                         seriesMetadataXML)

                # Store the series name in the MICROSCOPY_IMG_CONTAINER_NAME property
                dataset.setPropertyValue("MICROSCOPY_IMG_CONTAINER_NAME",
                                         allSeriesMetadata[i]["name"])

            # Set the (common) sample for the series
            dataset.setSample(sample)


    def processMicroscopyCompositeFile(self, microscopyCompositeFileNode,
                                       openBISExperiment):
        """Register the Microscopy Composite File using the parsed properties file.

        @param microscopyCompositeFileNode An XML node corresponding to a microscopy
        file (dataset)
        @param openBISExperiment An ISample object representing an Experiment
        """

        # Make sure to have a supported composite file type
        compositeFileType = microscopyCompositeFileNode.attrib.get("compositeFileType")

        if compositeFileType != "Leica TIFF Series":

            msg = "PROCESSOR::processMicroscopyCompositeFile(): " + \
                      "Invalid composite file type found: " + compositeFileType
            self._logger.error(msg)
            raise Exception(msg)

        else:

            self._logger.info("PROCESSOR::processMicroscopyCompositeFile(): " + \
                              "Processing " + compositeFileType)

        # Get the metadata for all series from the (processed) settings XML 
        allSeriesMetadata = []
        for series in microscopyCompositeFileNode:
            allSeriesMetadata.append(series.attrib)

        # Get the number of series
        num_series = len(microscopyCompositeFileNode)

        # Get the correct space where to create the sample
        identifier = openBISExperiment.getExperimentIdentifier()
        sample_space = identifier[1:identifier.find('/', 1)]
        self._logger.info("Creating sample with auto-generated code in space " + sample_space)

        # Create a sample for the dataset
        sample = self._transaction.createNewSampleWithGeneratedCode(sample_space,
                                                                    "MICROSCOPY_SAMPLE_TYPE")

        # Set the sample name
        name = microscopyCompositeFileNode.attrib.get("name")
        sample.setPropertyValue("MICROSCOPY_SAMPLE_NAME", name)

        # Set the sample description
        sampleDescr = microscopyCompositeFileNode.attrib.get("description")
        if sampleDescr is None:
            sampleDescr = ""
        sample.setPropertyValue("MICROSCOPY_SAMPLE_DESCRIPTION", sampleDescr)

        # Store the sample (total composite file) size in bytes
        datasetSize = microscopyCompositeFileNode.attrib.get("datasetSize")
        if datasetSize is not None:
            sample.setPropertyValue("MICROSCOPY_SAMPLE_SIZE_IN_BYTES", datasetSize)

        # Set the experiment
        sample.setExperiment(openBISExperiment)

        # Get the relative path to the containing folder
        relativeFolder = microscopyCompositeFileNode.attrib.get("relativeFolder")
        fullFolder = os.path.join(self._incoming.getAbsolutePath(), relativeFolder)

        # Log
        self._logger.info("PROCESSOR::processMicroscopyFile(): " + 
                          "Folder " + relativeFolder + " contains " + 
                           str(num_series) + " series.")

        # Get the series indices
        seriesIndices = microscopyCompositeFileNode.attrib.get("seriesIndices")
        seriesIndices = seriesIndices.split(",")

        # Register all series in the file
        image_data_set = None
        for i in range(num_series):

            # Series number
            seriesNum = seriesIndices[i]

            # Create a configuration object
            if compositeFileType == "Leica TIFF Series":

                compositeDatasetConfig = LeicaTIFFSeriesCompositeDatasetConfig(allSeriesMetadata,
                                                                               seriesIndices,
                                                                               self._logger,
                                                                               seriesNum)
            else:
                
                msg = "PROCESSOR::processMicroscopyCompositeFile(): " + \
                "Invalid composite file type found: " + compositeFileType
                self._logger.error(msg)
                raise Exception(msg)

            # Extract the metadata associated to this series and convert it to
            # XML to store it in the MICROSCOPY_IMG_CONTAINER_METADATA property
            # of the MICROSCOPY_IMG_CONTAINER_METADATA (series) dataset type
            seriesMetadataXML = self.dictToXML(allSeriesMetadata[i])

            # Register all series in the composite file (folder)
            if image_data_set is None:

                # Log
                self._logger.info("PROCESSOR::processCompositeMicroscopyFile(): " + 
                                  "Creating new image dataset for folder " + 
                                   str(fullFolder) + " and series " + str(seriesNum))

                # Create a dataset
                dataset = self._transaction.createNewImageDataSet(compositeDatasetConfig,
                                                                  java.io.File(fullFolder))

                # Store the metadata in the MICROSCOPY_IMG_CONTAINER_METADATA property
                # TODO: Get the store the metadata information
                dataset.setPropertyValue("MICROSCOPY_IMG_CONTAINER_METADATA",
                                         seriesMetadataXML)

                # Store the series name in the MICROSCOPY_IMG_CONTAINER_NAME property
                # TODO Get and store the correct series name
                dataset.setPropertyValue("MICROSCOPY_IMG_CONTAINER_NAME",
                                         allSeriesMetadata[i]["name"])

                # Now store a reference to the first dataset
                image_data_set = dataset

                # Move the file
                self._transaction.moveFile(fullFolder, image_data_set)

            else:

                # Log
                self._logger.info("PROCESSOR::processCompositeMicroscopyFile(): " + 
                                  "Appending series " + str(i) + " to dataset " +
                                  str(image_data_set))

                # Create an image dataset that points to an existing one
                # (and points to its file)
                dataset = self._transaction.createNewImageDataSetFromDataSet(compositeDatasetConfig,
                                                                             image_data_set)

                # Store the metadata in the MICROSCOPY_IMG_CONTAINER_METADATA property
                dataset.setPropertyValue("MICROSCOPY_IMG_CONTAINER_METADATA", seriesMetadataXML)

                # Store the series name in the MICROSCOPY_IMG_CONTAINER_NAME property
                dataset.setPropertyValue("MICROSCOPY_IMG_CONTAINER_NAME", "Series_" + str(seriesNum))


            # Set the (common) sample for the series
            dataset.setSample(sample)


    def register(self, tree):
        """Register the Experiment using the parsed properties file.

        @param tree ElementTree parsed from the properties XML file
        """

        # Get the root node (obitXML)
        root = tree.getroot()

        # Store the username
        self._username = root.attrib.get("userName")

        # Store the machine name
        machinename = root.attrib.get("machineName")
        if machinename is None:
            machinename = ""
        self._machinename = machinename        

        # Iterate over the children (Experiments)
        for experimentNode in root:

            # The tag of the immediate children of the root experimentNode
            # must be Experiment
            if experimentNode.tag != "Experiment":
                msg = "PROCESSOR::register(): " + \
                      "Expected Experiment node, found " + experimentNode.tag
                self._logger.error(msg)
                raise Exception(msg)

            # Process an Experiment XML node and get/create an IExperimentUpdatable
            openBISExperiment = self.processExperiment(experimentNode,
                                                       "MICROSCOPY_EXPERIMENT")

            # Process children of the Experiment
            for fileNode in experimentNode:

                if fileNode.tag == "MicroscopyFile":

                    # Process the MicroscopyFile node
                    self.processMicroscopyFile(fileNode, openBISExperiment)

                elif fileNode.tag == "MicroscopyCompositeFile":

                    # Process the MicroscopyCompositeFile node
                    self.processMicroscopyCompositeFile(fileNode, openBISExperiment)

                    # Inform
                    self._logger.info("Processed composite file")

                else:

                    msg = "PROCESSOR::register(): " + \
                    "Expected either MicroscopyFile or MicroscopyCompositeFile " + \
                    "node; found instead " + fileNode.tag + ")!"
                    self._logger.error(msg)
                    raise Exception(msg)

        # Log that we are finished with the registration
        self._logger.info("PROCESSOR::register(): " + 
                          "Registration completed")


    def retrieveOrCreateTags(self, tagList):
        """Retrieve or create the tags (metaprojects) with specified names."""

        # Initialize openBISTags list
        openBISTags = []

        # Make sure tagList is not None
        if tagList is None:
            return []

        # Get the individual tag names (with no blank spaces)
        tags = ["".join(t.strip()) for t in tagList.split(",")]

        # Process all tags (metaprojects)
        for tag in tags:
            if len(tag) == 0:
                continue

            # Retrieve the tag (metaproject)
            metaproject = self._transaction.getMetaproject(tag, self._username)
            if metaproject is None:

                # Create the tag (metaproject)
                self._logger.info("Creating metaproject " + tag)

                metaproject = self._transaction.createNewMetaproject(tag,
                                                                     "",
                                                                     self._username)

                # Check that creation was succcessful
                if metaproject is None:
                    msg = "Could not create metaproject " + tag + \
                    "for user " + self._username
                    self._logger.error(msg)
                    raise Exception(msg)

            # Add the created metaproject to the list
            openBISTags.append(metaproject)

        return openBISTags


    def run(self):
        """Run the registration."""

        # Make sure that incoming is a folder
        if not self._incoming.isDirectory():
            msg = "PROCESSOR::run(): " + \
            "Incoming MUST be a folder!"
            self._logger.error(msg)
            raise Exception(msg)

        # Log
        self._logger.info("PROCESSOR::run(): " + 
                          "Incoming folder: " + 
                          self._incoming.getAbsolutePath())

        # There must be just one subfolder: the user subfolder
        subFolders = self.getSubFolders()
        if len(subFolders) != 1:
            msg = "PROCESSOR::run(): " + \
            "Expected user subfolder!"
            self._logger.error(msg)
            raise Exception(msg)

        # Set the user folder
        userFolder = os.path.join(self._incoming.getAbsolutePath(),
                                  subFolders[0])

        # In the user subfolder we must find the data_structure.ois file
        dataFileName = os.path.join(userFolder, "data_structure.ois")
        if not os.path.exists(dataFileName):
            msg = "PROCESSOR::run(): " + \
            "File data_structure.ois not found!"
            self._logger.error(msg)
            raise Exception(msg)

        # Now read the data structure file and store all the pointers to
        # the properties files. The paths are stored relative to self._incoming,
        # so we can easily build the full file paths.
        propertiesFileList = []
        f = open(dataFileName)
        try:
            for line in f:
                line = re.sub('[\r\n]', '', line)
                propertiesFile = os.path.join(self._incoming.getAbsolutePath(),
                                              line)
                propertiesFileList.append(propertiesFile)
                self._logger.info("PROCESSOR::run(): " + 
                                  "Found: " + str(propertiesFile))
        finally:
            f.close()

        # Process (and ultimately register) all experiments
        for propertiesFile in propertiesFileList:
            # Log
            self._logger.info("PROCESSOR::run(): " + 
                              "Processing: " + propertiesFile)

            # Read the properties file into an ElementTree
            tree = ET.parse(propertiesFile)

            # Now register the experiment
            self.register(tree)
