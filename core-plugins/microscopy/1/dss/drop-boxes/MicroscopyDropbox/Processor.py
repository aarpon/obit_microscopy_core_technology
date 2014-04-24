"""
Created on Feb 20, 2014

@author: Aaron Ponti
"""

import java.io.File
import os
import re
import xml.etree.ElementTree as xml
from datetime import datetime
from BioFormatsProcessor import BioFormatsProcessor
from MicroscopySingleDatasetConfig import MicroscopySingleDatasetConfig

class Processor:
    """The Processor class performs all steps required for registering datasets
    from the assigned dropbox folder."""

    # A transaction object passed by openBIS
    _transaction = None

    # The incoming folder to process (a java.io.File object)
    _incoming = ""

    # The logger
    _logger = None

    # Constructor
    def __init__(self, transaction, logger):

        # Store arguments
        self._transaction = transaction
        self._incoming = transaction.getIncoming()

        # Set up logger
        self._logger = logger

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

    def createExperiment(self, expId, expName,
                         expType="MICROSCOPY_EXPERIMENT"):
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

        # Create the experiment
        self._logger.info("Register experiment %s" % expId)
        exp = self._transaction.createNewExperiment(expId, expType)
        if not exp:
            msg = "Could not create experiment " + expId + "!"
            self._logger.error(msg)
            raise Exception(msg)
        else:
            self._logger.info("Created experiment with ID " + expId + ".")

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

        # Create the experiment (with corrected ID if needed: see above)
        openBISExperiment = self.createExperiment(openBISIdentifier,
                                                  expName, openBISExpType)
        if not openBISExperiment:
            msg = "Could not create experiment " + openBISIdentifier
            self._logger.error(msg)
            raise Exception(msg)

        # Set the date
        # TODO: Add this
        # openBISExperiment.setPropertyValue("MICROSCOPY_EXPERIMENT_DATE",
        #                                   expDate)

        # Set the description
        openBISExperiment.setPropertyValue("MICROSCOPY_EXPERIMENT_DESCRIPTION",
                                           description)

        # Set the acquisition hardware
        # TODO: Add this
        # openBISExperiment.setPropertyValue("MICROSCOPY_EXPERIMENT_ACQ_HARDWARE",
        #                                   acqHardware)

        # Set the acquisition software
        # TODO: Add this
        # openBISExperiment.setPropertyValue("MICROSCOPY_EXPERIMENT_ACQ_SOFTWARE",
        #                                   acqSoftware)

        # Set the experiment owner
        # TODO: Add this
        # openBISExperiment.setPropertyValue("MICROSCOPY_EXPERIMENT_OWNER",
        #                                   owner)

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

        # Instantiate a BioFormatsProcessor
        bioFormatsProcessor = BioFormatsProcessor(fileName, self._logger)

        # Extract and store metadata
        bioFormatsProcessor.extractMetadata()

        # Log the number of series found
        num_series = bioFormatsProcessor.getNumSeries()
        self._logger.info("File " + self._incoming.getName() + " contains " + str(num_series) + " series.")
        image_data_set = None
        for i in range(num_series):
            # Create a configuration object
            singleDatasetConfig = MicroscopySingleDatasetConfig(bioFormatsProcessor, self._logger, i)
            if image_data_set is None:
                dataset = self._transaction.createNewImageDataSet(singleDatasetConfig, java.io.File(fileName))
                image_data_set = dataset
                self._transaction.moveFile(fileName, image_data_set)
            else:
                dataset = self._transaction.createNewImageDataSetFromDataSet(singleDatasetConfig, image_data_set)
            sample = self._transaction.createNewSampleWithGeneratedCode("MICROSCOPY", "MICROSCOPY_SAMPLE_TYPE")
            sample.setExperiment(openBISExperiment)
            dataset.setSample(sample)
    

    def register(self, tree):
        """Register the Experiment using the parsed properties file.

        @param tree ElementTree parsed from the properties XML file
        """

        # Get the root node (obitXML)
        root = tree.getroot()

        # Iterate over the children (Experiments)
        for experimentNode in root:

            # The tag of the immediate children of the root experimentNode
            # must be Experiment
            if experimentNode.tag != "Experiment":
                msg = "Expected Experiment node, found " + experimentNode.tag
                self._logger.error(msg)
                raise Exception(msg)

            # Process an Experiment XML node and get/create an IExperimentUpdatable
            openBISExperiment = self.processExperiment(experimentNode,
                                                       "MICROSCOPY_EXPERIMENT")

            # Process children of the Experiment
            for microscopyFileNode in experimentNode:

                if microscopyFileNode.tag != "MicroscopyFile":
                    msg = "Expected MicroscopyFile node (found " + \
                          microscopyFileNode.tag + "!"
                    self._logger.error(msg)
                    raise Exception(msg)

                # Process the MicroscopyFile node
                self.processMicroscopyFile(microscopyFileNode, openBISExperiment)

        # Log that we are finished with the registration
        self._logger.info("REGISTER: Registration completed")


    def run(self):
        """Run the registration."""

        # Make sure that incoming is a folder
        if not self._incoming.isDirectory():
            msg = "Incoming MUST be a folder!"
            self._logger.error(msg)
            raise Exception(msg)

        # Log
        self._logger.info("Incoming folder: " + self._incoming.getAbsolutePath())

        # There must be just one subfolder: the user subfolder
        subFolders = self.getSubFolders()
        if len(subFolders) != 1:
            msg = "Expected user subfolder!"
            self._logger.error(msg)
            raise Exception(msg)

        # Set the user folder
        userFolder = os.path.join(self._incoming.getAbsolutePath(),
                                  subFolders[0])

        # In the user subfolder we must find the data_structure.ois file
        dataFileName = os.path.join(userFolder, "data_structure.ois")
        if not os.path.exists(dataFileName):
            msg = "File data_structure.ois not found!"
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
                self._logger.info("Found: " + str(propertiesFile))
        finally:
            f.close()

        # Process (and ultimately register) all experiments
        for propertiesFile in propertiesFileList:
            # Log
            self._logger.info("* * * Processing: " + propertiesFile)

            # Read the properties file into an ElementTree
            tree = xml.parse(propertiesFile)

            # Now register the experiment
            self.register(tree)
