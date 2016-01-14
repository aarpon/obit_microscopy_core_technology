# -*- coding: utf-8 -*-

'''
Aggregation plug-in to copy all microscopy files for a gvien experiment to the user folder.
@author: Aaron Ponti
'''

from ch.systemsx.cisd.openbis.generic.shared.api.v1.dto import SearchCriteria
from ch.systemsx.cisd.openbis.generic.shared.api.v1.dto import SearchSubCriteria
from ch.systemsx.cisd.openbis.generic.shared.api.v1.dto.SearchCriteria import MatchClause
from ch.systemsx.cisd.openbis.generic.shared.api.v1.dto.SearchCriteria import MatchClauseAttribute
import os
import subprocess
import sys
import re
import zipfile
import java.io.File
import logging
from ch.ethz.scu.obit.common.server.longrunning import LRCache
import uuid
from threading import Thread


def touch(full_file):
    """Touches a file.
    """
    f = open(full_file, 'w')
    f.close()
    

def c_unique(seq):
    """Implements 'unique' of a list.
    """
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if not (x in seen or seen_add(x))]

def zip_folder(folder_path, output_path):
    """Zip the contents of an entire folder recursively. Please notice that
    empty sub-folders will NOT be included in the archive.
    """

    # Note: os.path.relpath() does not exist in Jython.
    # target = os.path.relpath(folder_path, start=os.path.dirname(folder_path))
    target = folder_path[folder_path.rfind(os.sep) + 1:]

    # Simple trick to build relative paths
    root_len = folder_path.find(target)

    try:

        # Open zip file (no compression)
        zip_file = zipfile.ZipFile(output_path, 'w', zipfile.ZIP_STORED, allowZip64=True)

        # Now recurse into the folder
        for root, folders, files in os.walk(folder_path):

            # We do not process folders. This is only useful to store empty
            # folders to the archive, but 1) jython's zipfile implementation
            # throws:
            #
            #     Exception: [Errno 21] Is a directory <directory_name>
            #
            # when trying to write a directory to a zip file (in contrast to 
            # Python's implementation) and 2) oBIT does not export empty
            # folders in the first place.

            # Build the relative directory path (current root)
            relative_dir_path = os.path.abspath(root)[root_len:]

            # If a folder only contains a subfolder, we disrupt the hierarchy,
            # unless we add a file.
            if len(files) == 0:
                touch(os.path.join(root, '~'))
                files.append('~')

            # Include all files
            for file_name in files:
                
                # Full file path to add
                full_file_path = os.path.join(root, file_name)
                relative_file_path = os.path.join(relative_dir_path, file_name)

                # Workaround problem with file name encoding
                full_file_path = full_file_path.encode('latin-1')
                relative_file_path = relative_file_path.encode('latin-1')

                # Write to zip
                zip_file.write(full_file_path, relative_file_path, \
                               zipfile.ZIP_STORED)

    except IOError, message:
        raise Exception(message)

    except OSError, message:
        raise Exception(message)

    except zipfile.BadZipfile, message:
        raise Exception(message)

    finally:
        zip_file.close()


class Mover():
    """
    Takes care of organizing the files to be copied to the user folder and
    performs the actual copying.
    """

    def __init__(self, experimentId, sampleId, mode, userId, properties, logger):
        """Constructor
        
        experimentId: id of the experiment (must be specified)
        sampleId:     id of the sample (optional, if specified, the sample id
                      will be used in the search criteria; if set to "" only
                      the experiment id will be used as filter).
        mode:         "normal", "zip", or "hrm". If mode is "normal", the files
                      will be copied to the user folder; if mode is "zip", the
                      files will be packaged into a zip files and served for 
                      download via the browser; if mode is "hrm", the files
                      will be copied to the HRM source folder.
        userId:       user id.
        properties:   plug-in properties. 
             
        """

        # Logger
        self._logger = logger

        # Store the valid file extensions
        self._validExtensions = self._getValidExtensions()

        # Store properties
        self._properties = properties

        # Experiment identifier
        self._experimentId = experimentId

        # Get the experiment
        self._experiment = searchService.getExperiment(self._experimentId)

        # Sample identifier
        self._sampleId = sampleId

        # Get the sample
        self._sample = None
        if not self._sampleId == "":
            self._sample = searchService.getSample(self._sampleId)

        # Experiment code (alias)
        # If no / is found, _experimentCode will be the same as _experimentId
        self._experimentCode = self._experimentId[self._experimentId.rfind("/") + 1:]

        # User folder: depending on the 'mode' settings, the user folder changes
        if mode =="normal":
            
            # Standard user folder
            self._userFolder = os.path.join(self._properties['base_dir'], \
                                            userId, self._properties['export_dir'])
            
        elif mode == "zip":

            # Get the path to the user's Session Workspace
            sessionWorkspace = sessionWorkspaceProvider.getSessionWorkspace()

            # The user folder now will point to the Session Workspace
            self._userFolder = sessionWorkspace.absolutePath

        elif mode == "hrm":

            # Standard user folder
            self._userFolder = os.path.join(self._properties['hrm_base_dir'], \
                                            userId, self._properties['hrm_src_subdir'])

        else:
            raise Exception("Bad value for argument 'mode' (" + mode  +")")

        # Store the mode
        self._mode = mode

        # Make sure the use folder (with export subfolder) exists and has
        # the correct permissions
        if not os.path.isdir(self._userFolder):
            self._createDir(self._userFolder)

        # Experiment full path in user/tmp folder
        self._experimentPath = os.path.join(self._userFolder, self._experimentCode)

        # Info
        self._logger.info("Export experiment with code " + \
                          self._experimentCode + " to " + \
                          str(self._userFolder))
        self._logger.info("Export mode is " + self._mode)

        # Message (in case of error)
        self._message = "";

        # Keep track of the number of copied files
        self._numCopiedFiles = 0


    # Public methods
    # =========================================================================

    def process(self):
        """
        Finds the dataset that belongs to the experiment with stored id
        and copies it to the user folder. If the processing was successful,
        the method returns True. Otherwise, it returns False.
        """

        # Check that the experiment could be retrieved
        if self._experiment == None:
            self._message = "Could not retrieve experiment with " \
            "identifier " + self._experimentId + "!"
            self._logger.error(self._message)
            return False

        # At this stage we can create the experiment folder in the user dir
        if not self._createExperimentFolder():
            self._message = "Could not create experiment folder " + \
            self._experimentPath
            self._logger.error(self._message)
            return False

        # Now point the current path to the newly created experiment folder
        
        # And we copy the files contained in the Experiment
        return self._copyFilesForExperiment()


    def compressIfNeeded(self):
        """Compresses the exported experiment folder to a zip archive
        but only if the mode was "zip".
        """

        if self._mode == "zip":
            zip_folder(self._experimentPath, self.getZipArchiveFullPath())


    def getZipArchiveFullPath(self):
        """Return the full path of the zip archive (or "" if mode was "normal"
        or "hrm").
        """

        if self._mode == "zip":
            return self._experimentPath + ".zip"

        return ""


    def getZipArchiveFileName(self):
        """Return the file name of the zip archive without path."""

        if self._mode == "zip":
            fullFile = java.io.File(self.getZipArchiveFullPath())
            return fullFile.getName()

        return ""


    def getErrorMessage(self):
        """
        Return the error message (in case process() returned failure)
        """
        return self._message


    def getNumberOfCopiedFiles(self):
        """
        Return the number of copied files.
        """
        return self._numCopiedFiles


    def getRelativeExperimentPath(self):
        """
        Return the experiment path relative to the user folder.
        """
        return userId + "/" + \
            self._experimentPath[self._experimentPath.rfind(self._properties['export_dir']):]


    # Private methods
    # =========================================================================

    def _getValidExtensions(self):
        """Build an array with all valid microscopy file extensions."""

        ext = [ "nd2", "czi", "zvi", "lsm", "stk", "tif", "tiff", "lif",
                "liff", "ics", "ids", "ims", "oib", "oif", "ome", "r3d",
                "dicom", "dm3", "lei", "png", "jp2", "jpg", "1sc", "2",
                "2fl", "3", "4", "5", "acff", "afm", "aim", "al3d", "am",
                "amiramesh", "apl", "arf", "avi", "bip", "bmp", "c01",
                "cfg", "cr2", "crw", "cxd", "dat", "dcm", "dm2", "dti",
                "dv", "eps", "epsi", "exp", "fdf", "fff", "ffr", "fits",
                "flex", "fli", "frm", "gel", "gif", "grey", "hdr", "hed",
                "his", "htd", "html", "hx", "img", "inr", "ipl", "ipm",
                "ipw", "jpk", "jpx", "l2d", "labels", "lim", "mdb", "mea",
                "mnc", "mng", "mod", "mov", "mrc", "mrw", "mtb", "mvd2",
                "naf", "nd", "ndpi", "nef", "nhdr", "nrrd", "obsep", "par",
                "pcx", "pds", "pgm", "pic", "pict", "pnl", "pr3", "ps",
                "psd", "raw", "res", "scn", "sdt", "seq", "sld", "sm2",
                "sm3", "spi", "stp", "svs", "sxm", "tfr", "tga", "tnb",
                "top", "txt", "v", "vms", "vsi", "vws", "wat", "xdce",
                "xml", "xqd", "xqf", "xv", "xys", "zfp", "zfr" ]

        return ext


    def _copyFilesForExperiment(self):
        """
        Copies the microscopy files in the experiment to the user directory.
        Folders are copied recursively.

        Returns True for success. In case of error, returns False and sets
        the error message in self._message -- to be retrieved with the
        getErrorMessage() method.
        """

        # Get the datasets for the experiment
        dataSets = self._getDataSetsForExperiment()
        if len(dataSets) == 0:
            self._logger.error("Experiment does not contain datasets.")
            return False

        # Get the files for the datasets
        dataSetFiles = self._getFilesForDataSets(dataSets)
        if len(dataSetFiles) == 0:
            self._logger.error("Datasets do not contain files.")
            return False

        # Since sub-series reference the same file, we make sure to keep
        # a unique version of the file list
        dataSetFiles = c_unique(dataSetFiles)

        # Copy the files to the experiment folder
        for micrFile in dataSetFiles:
            if os.path.isdir(micrFile):
                self._copyDir(micrFile, self._experimentPath)
            else:
                self._copyFile(micrFile, self._experimentPath)

        # Return success
        return True


    def _getDataSetsForExperiment(self):
        """
        Return a list of datasets belonging to the experiment and optionally
        to the sample. If the sample ID is empty, only the experiment is used
        in the search criteria.
        If none are found, return [].

        """

        # Set search criteria to retrieve all datasets for the experiment.
        # If the sample code is set, we also filter by it.
        searchCriteria = SearchCriteria()
        searchCriteria.addMatchClause(MatchClause.createAttributeMatch(MatchClauseAttribute.TYPE, "MICROSCOPY_IMG_CONTAINER"))
        expCriteria = SearchCriteria()
        expCriteria.addMatchClause(MatchClause.createAttributeMatch(MatchClauseAttribute.PERM_ID, self._experiment.permId))
        searchCriteria.addSubCriteria(SearchSubCriteria.createExperimentCriteria(expCriteria))
        if self._sample is not None:
            self._logger.info("Filter by sample " + self._sampleId)
            sampleCriteria = SearchCriteria()
            sampleCriteria.addMatchClause(MatchClause.createAttributeMatch(MatchClauseAttribute.PERM_ID, self._sample.permId))
            searchCriteria.addSubCriteria(SearchSubCriteria.createSampleCriteria(sampleCriteria))

        dataSets = searchService.searchForDataSets(searchCriteria)

        if len(dataSets) == 0:
            dataSets = []
            self._message = "Could not retrieve datasets for experiment " \
            "with id " + self._experimentId
            if self._sampleId != "":
                self._message = self._message + " and sample with id " + \
                self._sampleId
            self._logger.error(self._message)

        # Return
        return dataSets


    def _getFilesForDataSets(self, dataSets):
        """
        Get the list of microscopy file paths that correspond to the input list
        of datasets. If no files are found, returns [].
        """

        if dataSets == []:
            return []

        dataSetFiles = []
        for dataSet in dataSets:
            content = contentProvider.getContent(dataSet.getDataSetCode())
            nodes = content.listMatchingNodes("original", ".*")

            if nodes is not None:
                for node in nodes:
                    fileName = node.tryGetFile()
                    if fileName is not None:
                        fileName = str(fileName)
                        if os.path.isdir(str(fileName)):
                            dataSetFiles.append(fileName)
                        elif self._isValidMicroscopyFile(fileName):
                            dataSetFiles.append(fileName)
                        else:
                            raise("Unexpected file!")

        if len(dataSetFiles) == 0:
            self._message = "Could not retrieve dataset files!"
            self._logger.error(self._message)


        # Return the files
        return dataSetFiles


    def _isValidMicroscopyFile(self, fileName):
        """Checks whether the file has a compatible extension."""

        for validExt in self._validExtensions:
            fileName.lower().endswith("." + validExt)
            return True

        self._logger.error("File " + fileName + " is not a valid microscopy file.")
        return False


    def _copyFile(self, source, dstDir):
        """Copies the source file (with full path) to directory dstDir.
        We use a trick to preserve the NFSv4 ACLs: since copying the file
        loses them, we first touch the destination file to create it, and
        then we overwrite it.
        """
        dstFile = os.path.join(dstDir, os.path.basename(source))
        subprocess.call(["/bin/touch", dstFile])
        subprocess.call(["/bin/cp", source, dstDir])
        self._logger.info("Copying file " + source + " to " + dstDir)
        self._numCopiedFiles += 1

    def _copyDir(self, source, dstDir):
        """Copies the source directory (with full path) recursively to directory dstDir.
        """
        dstSubDir = os.path.join(dstDir, os.path.basename(source))
        self._logger.info("Creating directory " + dstDir)
        self._createDir(dstSubDir)

        # Info
        self._logger.info("Copying directory " + source + " to " + dstDir)

        # Now copy recursively (by preserving NFSv4 ACLs)
        files = os.listdir(source)
        for f in files:
            fullPath = os.path.join(source, f)
            if os.path.isdir(fullPath):
                self._copyDir(fullPath, dstSubDir)
            else:
                self._copyFile(fullPath, dstSubDir)


    def _createDir(self, dirFullPath):
        """Creates the passed directory (with full path).
        """
        
        # Inform
        self._logger.info("Creating directory " + dirFullPath)
        
        # Create dir
        os.makedirs(dirFullPath)


    def _createExperimentFolder(self):
        """
        Create the experiment folder. Notice that it uses information already
        stored in the object, but this info is filled in in the constructor, so
        it is safe to assume it is there if nothing major went wrong. In this
        case, the method will return False and no folder will be created.
        Otherwise, the method returns True.

        Please notice that if the experiment folder already exists, _{digit}
        will be appended to the folder name, to ensure that the folder is
        unique. The updated folder name will be stored in the _experimentPath
        property.
        """

        # This should not happen
        if self._experimentPath == "":
            return False

        # Make sure that the experiment folder does not already exist
        expPath = self._experimentPath

        # Does the folder already exist?
        if os.path.exists(expPath):
            counter = 1
            ok = False
            while not ok:
                tmpPath = expPath + "_" + str(counter)
                if not os.path.exists(tmpPath):
                    expPath = tmpPath
                    ok = True
                else:
                    counter += 1

        # Update the experiment path
        self._experimentPath = expPath

        # Inform
        self._logger.info("Output experiment folder: " + self._experimentPath)

        # Create the folder
        self._createDir(self._experimentPath)

        # Return success
        return True




# Parse properties file for custom settings
def parsePropertiesFile():
    """Parse properties file for custom plug-in settings."""

    filename = "../core-plugins/microscopy/1/dss/reporting-plugins/export_microscopy_datasets/plugin.properties"
    var_names = ['base_dir', 'export_dir', 'hrm_base_dir', 'hrm_src_subdir']

    properties = {}
    try:
        fp = open(filename, "r")
    except:
        return properties

    try:
        for line in fp:
            line = re.sub('[ \'\"\n]', '', line)
            parts = line.split("=")
            if len(parts) == 2:
                if parts[0] in var_names:
                    properties[parts[0]] = parts[1]
    finally:
        fp.close()

    # Check that all variables were found
    if len(properties.keys()) == 0:
        return None

    found_vars = properties.keys()

    for var_name in var_names:
        if var_name not in found_vars:
            return None

    # Everything found
    return properties


# Plug-in entry point
#
# Input parameters:
#
# uid      : job unique identifier (see below)
# expPermId: experiment identifier
# sampleId : sample identifier
# mode     : requested mode of operation: one of 'normal', 'hrm', zip'.
#
# This plug-in returns a table to the client with a different set of columns
# depending on whether the plug-in is called for the first time and the process
# is just started, or if it is queried for completeness at a later time.
#
# At the end of the first call, a table with following columns is returned:
#
# uid      : unique identifier of the running plug-in
# completed: indicated if the plug-in has finished. This is set to False in the 
#            first call.
#
# Later calls return a table with the following columns:
#
# uid      : unique identifier of the running plug-in. This was returned to
#            the client in the first call and was passed on again as a parameter.
#            Here it is returned again to make sure that client and server
#            always know which task they are talking about. 
# completed: True if the process has completed in the meanwhile, False if it 
#            is still running.
# success  : True if the process completed successfully, False otherwise.
# message  : error message in case success was False.
# nCopiedFiles: total number of copied files.
# relativeExpFolder: folder to the copied folder relative to the root of the
#            export folder.
# zipArchiveFileName: file name of the zip in case compression was requested.
# mode     : requested mode of operation.
def aggregate(parameters, tableBuilder):

    # Get the ID of the call if it already exists
    uid = parameters.get("uid");

    if uid is None or uid == "":

        # Create a unique id
        uid = str(uuid.uuid4())

        # Add the table headers
        tableBuilder.addHeader("uid")
        tableBuilder.addHeader("completed")

        # Fill in relevant information
        row = tableBuilder.addRow()
        row.setCell("uid", uid)
        row.setCell("completed", False)

        # Launch the actual process in a separate thread
        thread = Thread(target = aggregateProcess,
                        args = (parameters, tableBuilder, uid))
        thread.start()

        # Return immediately
        return

    # The process is already running in a separate thread. We get current
    # results and return them 
    resultToSend = LRCache.get(uid);
    if resultToSend is None:
        # This should not happen
        raise Exception("Could not retrieve results from result cache!")

    # Add the table headers
    tableBuilder.addHeader("uid")
    tableBuilder.addHeader("completed")
    tableBuilder.addHeader("success")
    tableBuilder.addHeader("message")
    tableBuilder.addHeader("nCopiedFiles")
    tableBuilder.addHeader("relativeExpFolder")
    tableBuilder.addHeader("zipArchiveFileName")
    tableBuilder.addHeader("mode")

    # Store current results in the table
    row = tableBuilder.addRow()
    row.setCell("uid", resultToSend["uid"])
    row.setCell("completed", resultToSend["completed"])
    row.setCell("success", resultToSend["success"])
    row.setCell("message", resultToSend["message"])
    row.setCell("nCopiedFiles", resultToSend["nCopiedFiles"]) 
    row.setCell("relativeExpFolder", resultToSend["relativeExpFolder"])
    row.setCell("zipArchiveFileName", resultToSend["zipArchiveFileName"])
    row.setCell("mode", resultToSend["mode"])


# Actual work process
def aggregateProcess(parameters, tableBuilder, uid):

    # Make sure to initialize and store the results. We need to have them since
    # most likely the client will try to retrieve them again before the process
    # is finished.
    resultToStore = {}
    resultToStore["uid"] = uid
    resultToStore["success"] = True
    resultToStore["completed"] = False
    resultToStore["message"] = ""
    resultToStore["nCopiedFiles"] = ""
    resultToStore["relativeExpFolder"] = ""
    resultToStore["zipArchiveFileName"] = ""
    resultToStore["mode"] = ""
    LRCache.set(uid, resultToStore)

    # Get path to containing folder
    # __file__ does not work (reliably) in Jython
    dbPath = "../core-plugins/microscopy/1/dss/reporting-plugins/export_microscopy_datasets"

    # Path to the logs subfolder
    logPath = os.path.join(dbPath, "logs")

    # Make sure the logs subforder exist
    if not os.path.exists(logPath):
        os.makedirs(logPath)

    # Path for the log file
    logFile = os.path.join(logPath, "log.txt")

    # Set up logging
    logging.basicConfig(filename=logFile, level=logging.DEBUG, 
                        format='%(asctime)-15s %(levelname)s: %(message)s')
    logger = logging.getLogger()

    # Get parameters from plugin.properties
    properties = parsePropertiesFile()
    if properties is None:
        raise Exception("Could not process plugin.properties")

    # Get the experiment identifier
    experimentId = parameters.get("experimentId")

    # Get the sample identifier
    sampleId = parameters.get("sampleId")

    # Get the mode
    mode = parameters.get("mode")

    # Info
    logger.info("Aggregation plug-in called with following parameters:")
    logger.info("experimentId = " + experimentId)
    logger.info("sampleId     = " + sampleId)
    logger.info("mode         = " + mode)
    logger.info("userId       = " + userId)
    logger.info("Aggregation plugin properties:")
    logger.info("properties   = " + str(properties))

    # Instantiate the Mover object - userId is a global variable
    # made available to the aggregation plug-in
    mover = Mover(experimentId, sampleId, mode, userId, properties, logger)

    # Process
    success = mover.process()

    # Compress
    if mode == "zip":
        mover.compressIfNeeded()

    # Get some results info
    nCopiedFiles = mover.getNumberOfCopiedFiles()
    errorMessage = mover.getErrorMessage();
    relativeExpFolder = mover.getRelativeExperimentPath()
    zipFileName = mover.getZipArchiveFileName()

    # Update results and store them
    resultToStore["uid"] = uid
    resultToStore["completed"] = True
    resultToStore["success"] = success
    resultToStore["message"] = errorMessage
    resultToStore["nCopiedFiles"] = nCopiedFiles
    resultToStore["relativeExpFolder"] = relativeExpFolder
    resultToStore["zipArchiveFileName"] = zipFileName
    resultToStore["mode"] = mode
    LRCache.set(uid, resultToStore)

    # Email result to the user
    if success == True:
        
        subject = "Microscopy: successfully processed requested data"
        
        if nCopiedFiles == 1:
            snip = "One file was "
        else:
            snip = str(nCopiedFiles) + " files were "

        if mode == "normal":
            body = snip + "successfully exported to {...}/" + relativeExpFolder + "."
        elif mode == "hrm":
            body = snip + "successfully exported to your HRM source folder."
        else:
            body = snip + "successfully packaged for download: " + zipFileName
            
    else:
        subject = "Microscopy: error processing request!"
        body = "Sorry, there was an error processing your request. " + \
        "Please send your administrator the following report:\n\n" + \
        "\"" + errorMessage + "\"\n"

    # Send
    try:
        mailService.createEmailSender().withSubject(subject).withBody(body).send()
    except:
        sys.stderr.write("export_microscopy_datasets: Failure sending email to user!")
