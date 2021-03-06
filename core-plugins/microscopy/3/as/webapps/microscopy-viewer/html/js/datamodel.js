/**
 * DataModel class
 *
 * @author Aaron Ponti
 *
 */


/**
 * Define a model class to hold the microscopy data.
 */
function DataModel() {

    "use strict";

    // Create a context object to access the context information
    this.context = new openbisWebAppContext();

    // Create an OpenBIS facade to call JSON RPC services
    this.openbisServer = new openbis("/openbis");

    // Reuse the current sessionId that we received in the context for
    // all the facade calls
    this.openbisServer.useSession(this.context.getSessionId());

    // Sample identifier
    this.microscopySampleId = this.context.getEntityIdentifier();

    // Sample perm ID
    this.microscopySamplePermId = this.context.getEntityPermId();

    // Sample type
    this.microscopySampleType = this.context.getEntityType();

    // Sample
    this.microscopySample = null;

    // openBIS experiment identifier
    this.experimentId = null;

    // MICROSCOPY_EXPERIMENT sample (parent of the MICROSCOPY_SAMPLE_TYPE
    // sample returned by the context)
    this.microscopyExperimentSample = null;

    // MICROSCOPY_EXPERIMENT sample name
    this.microscopyExperimentSampleName = "";

    // Datasets and dataset codes
    this.dataSets = [];
    this.dataSetCodes = [];

    // Does the experiment contain accessory files?
    this.accessoryFileDatasets = [];

    // Alias
    var dataModelObj = this;

    // Initialize all information concerning this sample
    this.initData(function (response) {

        if (response.hasOwnProperty("error")) {

            // Server returned an error
            dataModelObj.microscopySample = null;
            dataModelObj.microscopySampleId = null;
            dataModelObj.microscopySamplePermId = null;
            dataModelObj.microscopyExperimentSample = null;
            dataModelObj.microscopyExperimentSampleName = "Error: could not retrieve experiment!";

            // Initialize the experiment view
            DATAVIEWER.initView();

        } else {

            // Check that we got the sample associated with the openbisWebAppContext().getEntityIdentifier()
            if (response.result && response.result.length === 1) {

                // Store the sample object
                dataModelObj.microscopySample = response.result[0];

                // Store the openBIS experiment ID
                dataModelObj.experimentId = dataModelObj.microscopySample.experimentIdentifierOrNull;

                // Store the MICROSCOPY_EXPERIMENT sample object
                dataModelObj.microscopyExperimentSample = dataModelObj.microscopySample.parents[0];

                // Store the MICROSCOPY_EXPERIMENT_NAME property of the MICROSCOPY_EXPERIMENT sample
                dataModelObj.microscopyExperimentSampleName =
                    dataModelObj.microscopyExperimentSample.properties.MICROSCOPY_EXPERIMENT_NAME;

                // Now retrieve the list of datasets for the experiment and sample
                dataModelObj.getDataSetsForSampleAndExperiment(function (response) {

                    if (response.hasOwnProperty("error")) {
                        // Server returned an error
                        DATAVIEWER.displayStatus(response.error, "error");
                    } else {

                        // Store the datasets
                        if (response.result.length === 0) {

                            var msg = "No datasets found for experiment with code " +
                                dataModelObj.microscopyExperimentSample.code;
                            DATAVIEWER.displayStatus(msg, "error");

                        } else {

                            // Put dataset codes into an array
                            var dataSetCodes = [];
                            for (i = 0; i < response.result.length; i++) {
                                dataSetCodes.push(response.result[i].code)
                            }

                            // Sort by code
                            dataSetCodes.sort();

                            // Store
                            dataModelObj.dataSetCodes = dataSetCodes;

                            // Sort and store the datasets as well
                            dataModelObj.dataSets = [];
                            var unsortedDataSets = response.result;
                            for (var i = 0; i < dataSetCodes.length; i++) {
                                for (var j = 0; j < unsortedDataSets.length; j++) {
                                    if (unsortedDataSets[j].code === dataSetCodes[i]) {
                                        // Found. Add it to the datasets and remove it from the unsorted list
                                        dataModelObj.dataSets.push(unsortedDataSets[j]);
                                        unsortedDataSets.splice(j, 1);
                                        break;
                                    }
                                }
                            }

                            // Does the experiment contain accessory files?
                            dataModelObj.experimentContainsAccessoryFiles(function (response) {

                                // Store the datasets
                                if (response.hasOwnProperty("error")) {

                                    var msg = "Could not retrieve list of accessory files for experiment!";
                                    DATAVIEWER.displayStatus(msg, "error");

                                } else {

                                    // Store the list of accessory datasets
                                    dataModelObj.accessoryFileDatasets = response.result;

                                    // Initialize the experiment view
                                    DATAVIEWER.initView();
                                }
                            });

                        }
                    }

                });

            } else {

                // Could not retrieve the sample object
                dataModelObj.microscopySample = null;
                dataModelObj.microscopySampleId = null;
                dataModelObj.microscopySamplePermId = null;
                dataModelObj.microscopyExperimentSample = null;
                dataModelObj.microscopyExperimentSampleName = "Error: could not retrieve experiment!";

                // Initialize the experiment view
                DATAVIEWER.initView();

            }
        }

    });
}

/**
 * Get all data relative to current sample
 * @param action Function callback.
 */
DataModel.prototype.initData = function (action) {

    // Search for the MICROSCOPY_SAMPLE_TYPE sample. Make sure to retrieve the parent samples as well
    var searchCriteria = new SearchCriteria();
    searchCriteria.addMatchClause(
        SearchCriteriaMatchClause.createAttributeMatch(
            "TYPE",
            this.microscopySampleType)
    );
    searchCriteria.addMatchClause(
        SearchCriteriaMatchClause.createAttributeMatch(
            "PERM_ID",
            this.microscopySamplePermId));

    this.openbisServer.searchForSamplesWithFetchOptions(searchCriteria,
        ["PROPERTIES", "PARENTS"], action);

};

/**
 * Get current experiment.
 * @param {Function} action Function callback
 */
DataModel.prototype.getMicroscopyExperimentSampleData = function (action) {
    // sampleId must be in an array: [sampleId]
    this.openbisServer.listExperimentsForIdentifiers(
        [this.experimentId], action);
};

/**
 * Get datasets for current experiments
 * @param action
 */
DataModel.prototype.getDataSetsForSampleAndExperiment = function (action) {

    // Sample criteria (sample of type "MICROSCOPY_SAMPLE_TYPE" and code sampleCode)
    var sampleCriteria = new SearchCriteria();
    sampleCriteria.addMatchClause(
        SearchCriteriaMatchClause.createAttributeMatch(
            "PERM_ID",
            this.microscopySamplePermId
        )
    );
    sampleCriteria.addMatchClause(
        SearchCriteriaMatchClause.createAttributeMatch(
            "TYPE",
            "MICROSCOPY_SAMPLE_TYPE"
        )
    );

    // Dataset criteria
    var datasetCriteria = new SearchCriteria();
    datasetCriteria.addMatchClause(
        SearchCriteriaMatchClause.createAttributeMatch(
            "TYPE",
            "MICROSCOPY_IMG_CONTAINER"
        )
    );

    // Add sample and experiment search criteria as subcriteria
    datasetCriteria.addSubCriteria(
        SearchSubCriteria.createSampleCriteria(sampleCriteria)
    );

    // Search
    this.openbisServer.searchForDataSets(datasetCriteria, action);

};

/**
 * Checks whether the experiment contains accessory files.
 * @param action
 */
DataModel.prototype.experimentContainsAccessoryFiles = function (action) {

    // Experiment criteria (experiment of type "COLLECTION" and code expCode)
    var experimentCriteria = new SearchCriteria();
    experimentCriteria.addMatchClause(
        SearchCriteriaMatchClause.createAttributeMatch(
            "TYPE",
            "COLLECTION"
        )
    );

    // Sample criteria (sample of type "MICROSCOPY_SAMPLE_TYPE" and permId microscopySamplePermId)
    var sampleCriteria = new SearchCriteria();
    sampleCriteria.addMatchClause(
        SearchCriteriaMatchClause.createAttributeMatch(
            "PERM_ID",
            this.microscopySamplePermId)
    );
    sampleCriteria.addMatchClause(
        SearchCriteriaMatchClause.createAttributeMatch(
            "TYPE",
            "MICROSCOPY_SAMPLE_TYPE")
    );

    // Dataset criteria
    var datasetCriteria = new SearchCriteria();
    datasetCriteria.addMatchClause(
        SearchCriteriaMatchClause.createAttributeMatch(
            "TYPE",
            "MICROSCOPY_ACCESSORY_FILE"
        )
    );

    // Add sample and experiment search criteria as subcriteria
    datasetCriteria.addSubCriteria(
        SearchSubCriteria.createSampleCriteria(sampleCriteria)
    );
    datasetCriteria.addSubCriteria(
        SearchSubCriteria.createExperimentCriteria(experimentCriteria)
    );

    // Search
    this.openbisServer.searchForDataSets(datasetCriteria, action);

};

/**
 * Call an aggregation plug-in to copy the datasets associated to the experiment and sample.
 * @param experimentId Experiment ID
 * @param sampleId Sample ID
 * @param mode Mode to be passed to the aggragation service.
 */
DataModel.prototype.copyDatasetsToUserDir = function (experimentId, expSamplePermId, samplePermId, mode) {

    // Add call to the aggregation service
    var parameters = {
        experimentId: experimentId,
        expSamplePermId: expSamplePermId,
        samplePermId: samplePermId,
        mode: mode
    };

    // Inform the user that we are about to process the request
    DATAVIEWER.displayStatus("Please wait while processing your request. This might take a while...", "info");

    // Must use global object
    DATAMODEL.openbisServer.createReportFromAggregationService(CONFIG['dataStoreServer'],
        "export_microscopy_datasets", parameters,
        DATAMODEL.processResultsFromExportDataSetsServerSidePlugin);
};

/**
 * Process the results returned from the copyDatasetsToUserDir() server-side plug-in
 * @param response JSON object
 */
DataModel.prototype.processResultsFromExportDataSetsServerSidePlugin = function (response) {

    var status;
    var unexpected = "Sorry, unexpected feedback from server " +
        "obtained. Please contact your administrator.";
    var level = "";
    var row;

    // Returned parameters
    var r_UID;
    var r_Completed;
    var r_Success;
    var r_ErrorMessage;
    var r_NCopiedFiles;
    var r_RelativeExpFolder;
    var r_ZipArchiveFileName;
    var r_Mode;

    // First check if we have an error
    if (response.error) {

        // Indeed there was an error.
        status = "Sorry, could not process request.";
        level = "error";
        r_Success = "0";

    } else {

        // No obvious error. Retrieve the results
        status = "";
        if (response.result.rows.length !== 1) {

            // Unexpected number of rows returned
            status = unexpected;
            level = "error";

        } else {

            // We have a (potentially) valid result
            row = response.result.rows[0];

            // Retrieve the uid
            r_UID = row[0].value;

            // Retrieve the 'completed' status
            r_Completed = row[1].value;

            // If the processing is not completed, we wait a few seconds and trigger the
            // server-side plug-in again. The interval is defined by the admin.
            if (r_Completed === "0") {

                // We only need the UID of the job
                parameters = {};
                parameters["uid"] = r_UID;

                // Call the plug-in
                setTimeout(function () {
                        DATAMODEL.openbisServer.createReportFromAggregationService(
                            CONFIG['dataStoreServer'],
                            "export_microscopy_datasets", parameters,
                            DATAMODEL.processResultsFromExportDataSetsServerSidePlugin)
                    },
                    parseInt(CONFIG['queryPluginStatusInterval']));

                // Return here
                return;

            } else {

                if (row.length !== 8) {

                    // Again, something is wrong with the returned results
                    status = unexpected;
                    level = "error";

                } else {

                    // Extract returned values for clarity
                    r_Success = row[2].value;
                    r_ErrorMessage = row[3].value;
                    r_NCopiedFiles = row[4].value;
                    r_RelativeExpFolder = row[5].value;
                    r_ZipArchiveFileName = row[6].value;
                    r_Mode = row[7].value;

                    if (r_Success === "1") {
                        var snip = "<b>Congratulations!</b>&nbsp;";
                        if (r_NCopiedFiles === 1) {
                            snip = snip +
                                "<span class=\"badge\">1</span> file was ";
                        } else {
                            snip = snip +
                                "<span class=\"badge\">" +
                                r_NCopiedFiles + "</span> files were ";
                        }
                        if (r_Mode === "normal") {
                            status = snip + "successfully exported to " +
                                "{...}/" + r_RelativeExpFolder + ".";
                        } else if (r_Mode === "hrm") {
                            status = snip + "successfully exported to your HRM source folder.";
                        } else {
                            // Add a placeholder to store the download URL.
                            status = snip + "successfully packaged. <span id=\"download_url_span\"></span>";
                        }
                        level = "success";
                    } else {
                        if (r_Mode === "normal") {
                            status = "Sorry, there was an error exporting " +
                                "to your user folder:<br /><br />\"" +
                                r_ErrorMessage + "\".";
                        } else {
                            status = "Sorry, there was an error packaging your files for download!";
                        }
                        level = "error";
                    }
                }
            }
        }
    }
    DATAVIEWER.displayStatus(status, level);

    // Retrieve the URL (asynchronously)
    if (r_Success === "1" && r_Mode === "zip") {
        DATAMODEL.openbisServer.createSessionWorkspaceDownloadUrl(r_ZipArchiveFileName,
            function (url) {
                var downloadString =
                    '<img src="img/download.png" alt="Download" height="32" width="32"/>&nbsp;<a href="' + url + '">' +
                    'Download</a>!';
                $("#download_url_span").html(downloadString);
            });
    }
};