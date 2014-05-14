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


def touch(full_file):
    """Touches a file.
    """
    f = open(full_file, 'w')
    f.close()
    

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
        zip_file = zipfile.ZipFile(output_path, 'w', zipfile.ZIP_STORED)
        
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

    def __init__(self, experimentId, mode, userId, properties):
        '''Constructor'''

        # Store properties
        self._properties = properties

        # Experiment identifier
        self._experimentId = experimentId

        # Experiment code
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

        else:
            raise Exception("Bad value for argument 'mode' (" + mode  +")")

        # Store the mode
        self._mode = mode

        # Make sure the use folder (with export subfolder) exists and has
        # the correct permissions
        if not os.path.isdir(self._userFolder):
            self._createDir(self._userFolder)

        # Get the experiment
        self._experiment = searchService.getExperiment(self._experimentId)

        # Experiment full path in user/tmp folder
        self._experimentPath = os.path.join(self._userFolder, self._experimentCode)

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
            return False

        # At this stage we can create the experiment folder in the user dir
        if not self._createExperimentFolder():
            self._message = "Could not create experiment folder " + \
            self._experimentPath
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
        """Return the full path of the zip archive (or "" if mode was "normal").
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

    def _copyFilesForExperiment(self):
        """
        Copies the microscopy files in the experiment to the user directory.

        Returns True for success. In case of error, returns False and sets
        the error message in self._message -- to be retrieved with the
        getErrorMessage() method.
        """

        # Get the datasets for the experiment
        dataSets = self._getDataSetsForExperiment()
        if len(dataSets) == 0:
            return False

        # Get the files for the datasets
        dataSetFiles = self._getFilesForDataSets(dataSets)
        if len(dataSetFiles) == 0:
            return False
        
        # Copy the files to the experiment folder
        for micrFile in dataSetFiles:
            self._copyFile(micrFile, self._experimentPath)

        # Return success
        return True


    def _getDataSetsForExperiment(self):
        """
        Return a list of datasets belonging to the experiment.
        If none are found, return [].

        """

        # Set search criteria to retrieve all datasets for the experiment
        searchCriteria = SearchCriteria()
        searchCriteria.addMatchClause(MatchClause.createAttributeMatch(MatchClauseAttribute.TYPE, "MICROSCOPY_IMG"))
        expCriteria = SearchCriteria()
        expCriteria.addMatchClause(MatchClause.createAttributeMatch(MatchClauseAttribute.CODE, self._experimentCode))
        searchCriteria.addSubCriteria(SearchSubCriteria.createExperimentCriteria(expCriteria))
        dataSets = searchService.searchForDataSets(searchCriteria)
        
        if len(dataSets) == 0:
            dataSets = []
            self._message = "Could not retrieve datasets for experiment " \
            "with code " + self._experimentCode + "."

        # Return
        return dataSets


    def _getFilesForDataSets(self, dataSets):
        """
        Get the list of microscopy file paths that correspond to the input list
        of datasets. If not files are found, returns [].
        """

        if dataSets == []:
            return []

        dataSetFiles = []
        for dataSet in dataSets:
            content = contentProvider.getContent(dataSet.getDataSetCode())
            nodes = content.listMatchingNodes("original", ".*\.nd2")
            if nodes is not None:
                for node in nodes:
                    fileName = node.tryGetFile()
                    if fileName is not None:
                        fileName = str(fileName)
                        if fileName.lower().endswith(".nd2"):
                            dataSetFiles.append(fileName)

        if len(dataSetFiles) == 0:
            self._message = "Could not retrieve dataset files!"

        # Return the files
        return dataSetFiles


    def _copyFile(self, source, dstDir):
        """Copies the source file (with full path) to directory dstDir.
        We use a trick to preserve the NFSv4 ACLs: since copying the file
        loses them, we first touch the destination file to create it, and
        then we overwrite it.
        """
        dstFile = os.path.join(dstDir, os.path.basename(source))
        subprocess.call(["/bin/touch", dstFile])
        subprocess.call(["/bin/cp", source, dstDir])
        self._numCopiedFiles += 1


    def _createDir(self, dirFullPath):
        """Creates the passed directory (with full path).
        """
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

        # Create the folder
        self._createDir(self._experimentPath)

        # Return success
        return True




# Parse properties file for custom settings
def parsePropertiesFile():
    """Parse properties file for custom plug-in settings."""

    filename = "../core-plugins/microscopy/1/dss/reporting-plugins/copy_microscopy_datasets_to_userdir/plugin.properties"
    var_names = ['base_dir', 'export_dir']

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
def aggregate(parameters, tableBuilder):

    # Get parameters from plugin.properties
    properties = parsePropertiesFile()
    if properties is None:
        raise Exception("Could not process plugin.properties")

    # Get the experiment identifier
    experimentId = parameters.get("experimentId")

    # Get the mode
    mode = parameters.get("mode")

    # Instantiate the Mover object - userId is a global variable
    # made available to the aggregation plug-in
    mover = Mover(experimentId, mode, userId, properties)

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

    # Add the table headers
    tableBuilder.addHeader("Success")
    tableBuilder.addHeader("Message")
    tableBuilder.addHeader("nCopiedFiles")
    tableBuilder.addHeader("relativeExpFolder")
    tableBuilder.addHeader("zipArchiveFileName")
    tableBuilder.addHeader("Mode")

    # Store the results in the table
    row = tableBuilder.addRow()
    row.setCell("Success", success)
    row.setCell("Message", errorMessage)
    row.setCell("nCopiedFiles", nCopiedFiles)
    row.setCell("relativeExpFolder", relativeExpFolder)
    row.setCell("zipArchiveFileName", zipFileName)
    row.setCell("Mode", mode)

    # Email result to the user
    if success == True:
        
        subject = "Microscopy: successfully processed requested data"
        
        if nCopiedFiles == 1:
            snip = "One file was "
        else:
            snip = str(nCopiedFiles) + " files were "

        if mode == "normal":
            body = snip + "successfully exported to {...}/" + relativeExpFolder + "."
        else:
            body = snip + "successfully packaged for download."
            
    else:
        subject = "Microscopy: error processing request!"
        body = "Sorry, there was an error processing your request. " + \
        "Please send your administrator the following report:\n\n" + \
        "\"" + errorMessage + "\"\n"

    # Send
    try:
        mailService.createEmailSender().withSubject(subject).withBody(body).send()
    except:
        sys.stderr.write("copy_microscopy_datasets_to_userdir: Failure sending email to user!")
