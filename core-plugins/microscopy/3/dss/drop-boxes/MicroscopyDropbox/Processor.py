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
from GenericTIFFSeriesCompositeDatasetConfig import GenericTIFFSeriesCompositeDatasetConfig
from LeicaTIFFSeriesCompositeDatasetConfig import LeicaTIFFSeriesCompositeDatasetConfig
from YouScopeExperimentCompositeDatasetConfig import YouScopeExperimentCompositeDatasetConfig
from VisitronNDCompositeDatasetConfig import VisitronNDCompositeDatasetConfig


class Processor:
    """The Processor class performs all steps required for registering datasets
    from the assigned dropbox folder."""

    # A transaction object passed by openBIS
    _transaction = None

    # The incoming folder to process (a java.io.File object)
    _incoming = ""

    # The user name
    _username = ""

    # The machine name
    _machinename = ""

    # The logger
    _logger = None

    # The version number
    __version__ = 2

    # Constructor
    def __init__(self, transaction, logger):

        # Store arguments
        self._transaction = transaction
        self._incoming = transaction.getIncoming()

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

    def createSample(self,
                     sampleIdentifier,
                     sampleType,
                     setExperiment=False,
                     openBISCollection=None):
        """Create a sample with given code.

        Depending on whether project samples are enabled in openBIS, the sample
        code will be created accordingly.

        @param sampleIdentifier The full identifier of the new sample.
        @param sampleType Type of the sample to be created.
        @param setExperiment (optional, default = False) Set to true, to assign the
               newly created sample to the openBISCollection collection.
        @param openBISCollection (optional, default = None) If setExperiment is set to
               true, a valid openBISCollection collection object must be passed.                      
        @return sample Created ISample
        """

        # The sample identifier must have 3 parts
        if sampleIdentifier[0] != "/":
            msg = "Bad sample identifier " + str(sampleIdentifier)
            self._logger.err(msg)
            raise Exception(msg)

        parts = sampleIdentifier[1:].split('/')
        if len(parts) != 3:
            msg = "Bad sample identifier " + str(sampleIdentifier)
            self._logger.err(msg)
            raise Exception(msg)

        if self._transaction.serverInformation.get('project-samples-enabled') == 'true':

            # The code is in the correct form "/SPACE/PROJECT/SAMPLE_CODE
            code = sampleIdentifier

        else:

            # The code must be brought to the form "/SPACE/SAMPLE_CODE
            code = parts[0] + "/" + parts[2]

        # Create the sample
        sample = self._transaction.createNewSample(code, sampleType)

        # Set the experiment (collection)?
        if setExperiment:
            if openBISCollection is not None:

                # Assign to collection
                sample.setExperiment(openBISCollection)

                # Inform
                self._logger.info("Assigned sample of type " + sampleType +
                                  " and identifier " + str(sample.getSampleIdentifier()) +
                                  " to collection with identifier " +
                                  str(openBISCollection.getExperimentIdentifier()))

            else:
                raise Exception("A valid Collection object must be provided!")

        return sample

    def createSampleWithGenCode(self,
                                spaceCode,
                                openBISCollection,
                                sampleType,
                                setExperiment=True):
        """Create a sample with automatically generated code.

        Depending on whether project samples are enabled in openBIS, the sample
        code will be created accordingly.

        @param spaceCode The code of space (the space must exist).
        @param openBISCollection The openBIS Collection object (must exist).
        @param sampleType Type of the sample to be created.
        @param setExperiment (optional, default = True) Set to true, to assign the
               newly created sample to the openBISCollection collection.        
        @return sample Created ISample
        """

        if self._transaction.serverInformation.get('project-samples-enabled') == 'true':

            identifier = openBISCollection.getExperimentIdentifier()
            project_identifier = identifier[:identifier.rfind('/')]
            sample = self._transaction.createNewProjectSampleWithGeneratedCode(project_identifier,
                                                                               sampleType)
        else:

            # Make sure there are not slashes in the spaceCode
            spaceCode = spaceCode.replace("/", "")

            # Create the sample
            sample = self._transaction.createNewSampleWithGeneratedCode(spaceCode,
                                                                        sampleType)

        # Set the experiment (collection)?
        if setExperiment:

            # Assign to collection
            sample.setExperiment(openBISCollection)

            # Inform
            self._logger.info("Assigned sample of type " + sampleType +
                              " and identifier " + str(sample.getSampleIdentifier()) +
                              " to collection with identifier " +
                              str(openBISCollection.getExperimentIdentifier()))

        return sample

    def getSubFolders(self):
        """Return a list of subfolders of the passed incoming directory.

        @return list of subfolders (String)
        """

        incomingStr = self._incoming.getAbsolutePath()
        return [name for name in os.listdir(incomingStr)
                if os.path.isdir(os.path.join(incomingStr, name))]

    def getOrCreateCollection(self, openBISCollectionIdentifier):
        """Retrieve or register an openBIS Collection with given identifier.

        @param openBISCollectionIdentifier The Collection's openBIS indentifier.
        @return IExperiment collection
        """

        # Try retrieving the collection
        collection = self._transaction.getExperiment(openBISCollectionIdentifier)

        # If the collection does not exist, create it
        if collection is None:

            # Create a new collection of type "COLLECTION"
            collection = self._transaction.createNewExperiment(openBISCollectionIdentifier,
                                                               "COLLECTION")
            if collection is None:
                msg = "PROCESSOR::getOrCreateCollection(): failed creating " + \
                      "collection with ID " + openBISCollectionIdentifier + "."
                self._logger.err(msg)
                raise Exception(msg)

            else:
                self._logger.info("PROCESSOR::getOrCreateCollection(): " +
                                  "Created collection with ID " + openBISCollectionIdentifier + ".")

                # The collection name is hard-coded to "Microscopy experiments collection"
                collectionName = "Microscopy experiments collection"

                # Set the collection name
                collection.setPropertyValue("$NAME", collectionName)

        return collection

    def processExperimentNode(self, experimentNode):
        """Register a MICROSCOPY_EXPERIMENT sample based on the Experiment XML node.

        @param experimentNode An XML node corresponding to a MICROSCOPY_EXPERIMENT (sample)
        @return ISample Sample of type MICROSCOPY_EXPERIMENT
        """

        # Get the openBIS collection identifier
        openBISCollectionIdentifier = experimentNode.attrib.get("openBISCollectionIdentifier")

        # Get the openBIS identifier
        openBISIdentifier = experimentNode.attrib.get("openBISIdentifier")

        # Get the experiment name
        expName = experimentNode.attrib.get("name")

        # Get the description
        description = experimentNode.attrib.get("description")

        # Get attachments
        attachments = experimentNode.attrib.get("attachments")

        # Make sure to keep the code length within the limits imposed by
        # openBIS for codes
        if len(openBISIdentifier) > 41:
            openBISIdentifier = openBISIdentifier[0:41]

        # Create univocal ID
        openBISIdentifier = openBISIdentifier + "_" + self.getCustomTimeStamp()

        # Get or create the collection with given identifier
        collection = self.getOrCreateCollection(openBISCollectionIdentifier)

        # Make sure to create a new sample of type "MICROSCOPY_EXPERIMENT" and
        # assign it to the collection
        openBISExperimentSample = self.createSample(openBISIdentifier,
                                                    "MICROSCOPY_EXPERIMENT",
                                                    setExperiment=True,
                                                    openBISCollection=collection)

        if openBISExperimentSample is None:
            msg = "PROCESSOR::processExperimentNode(): " + \
                  "Could not create MICROSCOPY_EXPERIMENT sample " + openBISIdentifier
            self._logger.error(msg)
            raise Exception(msg)
        else:
            self._logger.info("PROCESSOR::processExperimentNode(): " + \
                              "Created experiment sample with identifier " + openBISIdentifier)

        # Inform
        self._logger.info("PROCESSOR::processExperimentNode(): " + \
                          "Assigned experiment sample with identifier " + openBISIdentifier +
                          " to collection " + str(openBISExperimentSample.getExperiment().getExperimentIdentifier()))

        # Get comma-separated tag list
        tagList = experimentNode.attrib.get("tags")
        if tagList != None and tagList != "":

            # Add tags (create them if needed)
            openBISExperimentSample = self.registerTags(openBISExperimentSample, tagList)

        # Store the name (in both the MICROSCOPY_EXPERIMENT_NAME and NAME properties)
        # NAME is used by the ELN-LIMS user interface.
        openBISExperimentSample.setPropertyValue("$NAME", expName)
        openBISExperimentSample.setPropertyValue("MICROSCOPY_EXPERIMENT_NAME", expName)

        # Set the experiment version (to be the global __version__)
        openBISExperimentSample.setPropertyValue("MICROSCOPY_EXPERIMENT_VERSION",
                                                 str(self.__version__))

        # Set the description -- but only if is not empty.
        # This makes sure that the description of an already existing experiment
        # is not overridden by an empty string.
        if description != "":
            openBISExperimentSample.setPropertyValue("MICROSCOPY_EXPERIMENT_DESCRIPTION",
                                                     description)
        else:
            currentDescription = openBISExperimentSample.getPropertyValue("MICROSCOPY_EXPERIMENT_DESCRIPTION")
            if (currentDescription is None or currentDescription == ""):
                openBISExperimentSample.setPropertyValue("MICROSCOPY_EXPERIMENT_DESCRIPTION", "")

        # Set the acquisition hardware friendly name
        openBISExperimentSample.setPropertyValue("MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME",
                                                 self._machinename)

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
                attachmentFilePath = os.path.join(self._incoming.getAbsolutePath(), f)

                # Extract the file name
                attachmentFileName = os.path.basename(attachmentFilePath)

                # Create a dataset of type ATTACHMENT and add it to the
                # MICROSCOPY_EXPERIMENT sample.
                # We do not add it directly to the Collection to comply with the way
                # ELN-LIMS displays the structure in the navigation.
                attachmentDataSet = self._transaction.createNewDataSet("ATTACHMENT")
                self._transaction.moveFile(attachmentFilePath, attachmentDataSet)
                attachmentDataSet.setPropertyValue("$NAME", attachmentFileName)
                attachmentDataSet.setSample(openBISExperimentSample)

        # Return the openBIS Experiment object
        return openBISExperimentSample

    def processMicroscopyFile(self, microscopyFileNode, openBISSample):
        """Register the Microscopy File using the parsed properties file.

        @param microscopyFileNode An XML node corresponding to a microscopy 
               file (dataset)
        @param openBISSample An ISample object representing an Experiment
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

        # Create the sample
        sample = self.createSampleWithGenCode(openBISSample.getSampleIdentifier(),
                                              openBISSample.getExperiment(),
                                              "MICROSCOPY_SAMPLE_TYPE",
                                              setExperiment=True)

        # Inform
        self._logger.info("PROCESSOR::processMicroscopyFile(): " + \
                          "Successfully created sample of type MICROSCOPY_SAMPLE_TYPE and " + \
                          "identifier " + sample.getSampleIdentifier())

        # Set the sample name
        file_name_without_path = relativeFileName[relativeFileName.rfind('/') + 1:]
        sample.setPropertyValue("MICROSCOPY_SAMPLE_NAME", file_name_without_path)
        sample.setPropertyValue("$NAME", file_name_without_path)

        # Set the sample description
        sampleDescr = microscopyFileNode.attrib.get("description")
        if sampleDescr is None:
            sampleDescr = ""
        sample.setPropertyValue("MICROSCOPY_SAMPLE_DESCRIPTION", sampleDescr)

        # Store the sample (file) size in bytes
        datasetSize = microscopyFileNode.attrib.get("datasetSize")
        if datasetSize is not None:
            sample.setPropertyValue("MICROSCOPY_SAMPLE_SIZE_IN_BYTES", datasetSize)

        # Inform
        self._logger.info("PROCESSOR::processMicroscopyFile(): " + \
                          "Assigning sample of type MICROSCOPY_SAMPLE_TYPE and " +
                          "identifier " + str(sample.getSampleIdentifier()) + " as " +
                          "child of sample of type " + str(openBISSample.getSampleType()) +
                          " and identifier " + str(openBISSample.getSampleIdentifier()))

        # Set the parent MICROSCOPY_EXPERIMENT sample
        sample.setParentSampleIdentifiers([openBISSample.getSampleIdentifier()])

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
            self._logger.info("PROCESSOR::processMicroscopyFile(): " +
                              "Series metadata (XML): " + str(seriesMetadataXML))

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

                # Store the series name in the $NAME property
                dataset.setPropertyValue("$NAME", allSeriesMetadata[i]["name"])

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

                # Store the series name in the $NAME property
                dataset.setPropertyValue("$NAME", allSeriesMetadata[i]["name"])

            # Set the (common) sample for the series
            dataset.establishSampleLinkForContainedDataSets()
            dataset.setSample(sample)

            # Inform
            self._logger.info("PROCESSOR::processMicroscopyFile(): " +
                              "Dataset of type " + str(dataset.getDataSetType()) +
                              " and permId " + str(sample.getPermId()) +
                              " assigned to sample of type " + str(sample.getSampleType()) +
                              " and identifier " + str(sample.getSampleIdentifier()))

    def processMicroscopyCompositeFile(self, microscopyCompositeFileNode,
                                       openBISSample):
        """Register the Microscopy Composite File using the parsed properties file.

        @param microscopyCompositeFileNode An XML node corresponding to a microscopy
        file (dataset)
        @param openBISSample An ISample object representing an Experiment
        """

        # Make sure to have a supported composite file type
        compositeFileType = microscopyCompositeFileNode.attrib.get("compositeFileType")

        if compositeFileType != "Leica TIFF Series" and \
                compositeFileType != "Generic TIFF Series" and \
                compositeFileType != "YouScope Experiment" and \
                compositeFileType != "Visitron ND":

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

        # Create the sample
        sample = self.createSampleWithGenCode(openBISSample.getSampleIdentifier(),
                                              openBISSample.getExperiment(),
                                              "MICROSCOPY_SAMPLE_TYPE",
                                              setExperiment=True)

        # Inform
        self._logger.info("PROCESSOR::processMicroscopyCompositeFile(): " + \
                "Successfully created sample of type MICROSCOPY_SAMPLE_TYPE and " + \
                "identifier " + sample.getSampleIdentifier())

        # Set the sample name
        name = microscopyCompositeFileNode.attrib.get("name")
        sample.setPropertyValue("MICROSCOPY_SAMPLE_NAME", name)
        sample.setPropertyValue("$NAME", name)

        # Set the sample description
        sampleDescr = microscopyCompositeFileNode.attrib.get("description")
        if sampleDescr is None:
            sampleDescr = ""
        sample.setPropertyValue("MICROSCOPY_SAMPLE_DESCRIPTION", sampleDescr)

        # Store the sample (total composite file) size in bytes
        datasetSize = microscopyCompositeFileNode.attrib.get("datasetSize")
        if datasetSize is not None:
            sample.setPropertyValue("MICROSCOPY_SAMPLE_SIZE_IN_BYTES", datasetSize)

        # Set the parent MICROSCOPY_EXPERIMENT sample
        sample.setParentSampleIdentifiers([openBISSample.getSampleIdentifier()])

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

        # For YouScope experiments, process the images.csv file and register the
        # accessory files in the root of the experiment
        if compositeFileType == "YouScope Experiment":
            # Build image file table
            csvTable = YouScopeExperimentCompositeDatasetConfig.buildImagesCSVTable(fullFolder + "/images.csv",
                                                                                    self._logger)

        # Register all series in the file
        image_data_set = None
        for i in range(num_series):

            # Series number
            seriesNum = seriesIndices[i]

            self._logger.info("PROCESSOR::processMicroscopyCompositeFile(): " + \
                              "Processing series " + str(seriesNum) + " of " + str(num_series))

            # Create a configuration object
            if compositeFileType == "Leica TIFF Series":

                compositeDatasetConfig = LeicaTIFFSeriesCompositeDatasetConfig(allSeriesMetadata,
                                                                               seriesIndices,
                                                                               self._logger,
                                                                               seriesNum)

            elif compositeFileType == "Generic TIFF Series":

                compositeDatasetConfig = GenericTIFFSeriesCompositeDatasetConfig(allSeriesMetadata,
                                                                                 seriesIndices,
                                                                                 self._logger,
                                                                                 seriesNum)

            elif compositeFileType == "YouScope Experiment":

                compositeDatasetConfig = YouScopeExperimentCompositeDatasetConfig(csvTable,
                                                                                  allSeriesMetadata,
                                                                                  seriesIndices,
                                                                                  self._logger,
                                                                                  seriesNum)

            elif compositeFileType == "Visitron ND":

                compositeDatasetConfig = VisitronNDCompositeDatasetConfig(allSeriesMetadata,
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
                dataset.setPropertyValue("MICROSCOPY_IMG_CONTAINER_NAME",
                                         allSeriesMetadata[i]["name"])

                # Store the series name in the $NAME property
                dataset.setPropertyValue("$NAME", allSeriesMetadata[i]["name"])

                # Register the accessory files for YouScope experiments
                if compositeFileType == "YouScope Experiment":
                    YouScopeExperimentCompositeDatasetConfig.registerAccessoryFilesAsDatasets(
                        fullFolder,
                        relativeFolder,
                        self._transaction,
                        openBISSample,
                        sample,
                        dataset,
                        self._logger)

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

                # Store the metadata in the MICROSCOPY_IMG_CONTAINER_METADATA and $NAME properties
                dataset.setPropertyValue("MICROSCOPY_IMG_CONTAINER_METADATA", seriesMetadataXML)

                # Store the series name in the MICROSCOPY_IMG_CONTAINER_NAME property
                if "name" in allSeriesMetadata[i] and allSeriesMetadata[i]["name"] != "":
                    self._logger.info("PROCESSOR::processMicroscopyCompositeFile(): " + \
                                      "The series name is " + str(allSeriesMetadata[i]["name"]))
                    dataset.setPropertyValue("MICROSCOPY_IMG_CONTAINER_NAME", allSeriesMetadata[i]["name"])
                    dataset.setPropertyValue("$NAME", allSeriesMetadata[i]["name"])
                else:
                    self._logger.info("PROCESSOR::processMicroscopyCompositeFile(): " + \
                                      "Falling back to series name series_" + str(seriesNum))
                    dataset.setPropertyValue("MICROSCOPY_IMG_CONTAINER_NAME", "series_" + str(seriesNum))
                    dataset.setPropertyValue("$NAME", "series_" + str(seriesNum))

            # Set the (common) sample for the series
            dataset.establishSampleLinkForContainedDataSets()
            dataset.setSample(sample)

    def register(self, tree):
        """Register the Experiment using the parsed properties file.

        @param tree ElementTree parsed from the properties XML file
        """

        # Get the root node (obitXML)
        rootNode = tree.getroot()

        # Check the tag
        if rootNode.tag != "obitXML":
            msg = "PROCESSOR::register(): Unexpected properties root node tag '" + \
                  rootNode.tag + "'. Invalid file. Cannot process."
            self._logger.error(msg)
            raise Exception(msg)

        # Make sure that we have the expected version of the properties file
        file_version = rootNode.attrib.get("version")
        if file_version is None:
            msg = "PROCESSOR::register(): Expected properties file version " + \
                  str(self.__version__) + ". This file is obsolete. Cannot process."
            self._logger.error(msg)
            raise Exception(msg)
        file_version = int(file_version)
        if file_version < self.__version__:
            msg = "PROCESSOR::register(): Expected properties file version " + \
                  str(self.__version__) + ". This file is obsolete. Cannot process."
            self._logger.error(msg)
            raise Exception(msg)

        # Store the username
        self._username = rootNode.attrib.get("userName")

        # Store the machine name
        machinename = rootNode.attrib.get("machineName")
        if machinename is None:
            machinename = ""
        self._machinename = machinename

        # Iterate over the children (Experiment nodes that map to MICROSCOPY_EXPERIMENT samples)
        for experimentNode in rootNode:

            # The tag of the immediate children of the root experimentNode
            # must be Experiment
            if experimentNode.tag != "Experiment":
                msg = "PROCESSOR::register(): " + \
                      "Expected Experiment node, found " + experimentNode.tag
                self._logger.error(msg)
                raise Exception(msg)

            # Process an Experiment XML node and get/create an ISample
            openBISExperimentSample = self.processExperimentNode(experimentNode)

            # Process children of the Experiment
            for fileNode in experimentNode:

                if fileNode.tag == "MicroscopyFile":

                    # Process the MicroscopyFile node
                    self.processMicroscopyFile(fileNode, openBISExperimentSample)

                elif fileNode.tag == "MicroscopyCompositeFile":

                    # Process the MicroscopyCompositeFile node
                    self.processMicroscopyCompositeFile(fileNode,
                                                        openBISExperimentSample)

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

    def registerTags(self, openBISExperimentSample, tagList):
        """Register the tags as parent samples of type ORGANIZATION_UNIT."""

        # Make sure tagList is not None
        if tagList is None:
            return openBISExperimentSample

        # Collect the parent sample identifiers
        tagSampleIdentifiers = []

        # Get the individual tag names (with no blank spaces)
        tags = ["".join(t.strip()) for t in tagList.split(",")]

        # Process all tags
        for tag in tags:
            if len(tag) == 0:
                continue

            # If the tag (sample of type "ORGANIZATION_UNIT") does not yet exist, create it
            sample = self._transaction.getSample(tag)
            if sample is None:
                sample = self._transaction.createNewSample(tag, "ORGANIZATION_UNIT")

            tagSampleIdentifiers.append(tag)

        # Add tag samples as parent
        openBISExperimentSample.setParentSampleIdentifiers(tagSampleIdentifiers)

        return openBISExperimentSample

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

