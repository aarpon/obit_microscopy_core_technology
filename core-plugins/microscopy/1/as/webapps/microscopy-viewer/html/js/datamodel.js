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
    this.sampleId = this.context.getEntityIdentifier();

    // Sample
    this.sample = null;

    // Experiment identifier
    this.expId = null;

    // Experiment object and name
    this.exp = null;
    this.expName = "";

    // Datasets and dataset codes
    this.dataSets = []
    this.dataSetCodes = [];

    // Alias
    var dataModelObj = this;

    // Initialize all information concerning this sample
    this.initData(function(response) {

        if (response.hasOwnProperty("error")) {

            // Server returned an error
            dataModelObj.sample = null;
            dataModelObj.expId = null;
            dataModelObj.exp = null;
            dataModelObj.expName = "Error: could not retrieve experiment!";

            // Initialize the experiment view
            DATAVIEWER.initView();

        } else {

            // Check that we got the sample associated with the openbisWebAppContext().getEntityIdentifier()
            if (response.result && response.result.length == 1) {

                // Store the sample object
                dataModelObj.sample = response.result[0];
                dataModelObj.expId = dataModelObj.sample.experimentIdentifierOrNull;

                // Now retrieve the experiment object
                dataModelObj.getExperimentData(function(response) {

                    if (response.hasOwnProperty("error")) {
                        // Server returned an error
                        dataModelObj.exp = null;
                        dataModelObj.expName = "Error: could not retrieve experiment!";
                    } else {
                        dataModelObj.exp = response.result[0];
                        dataModelObj.expName = dataModelObj.exp.properties.MICROSCOPY_EXPERIMENT_NAME;

                        // Now retrieve the list of datasets for the experiment and sample
                        dataModelObj.getDataSetsForSampleAndExperiment(function(response) {

                            if (response.hasOwnProperty("error")) {
                                // Server returned an error
                                DATAVIEWER.displayStatus(response.error, "error");
                            } else {

                                // Store the datasets
                                if (response.hasOwnProperty("error") || response.result.length == 0) {

                                    var msg = "No datasets found for experiment with code " +
                                        dataModelObj.exp.code;
                                    DATAVIEWER.displayStatus(msg, "error");

                                } else {

                                    // Put dataset codes into an array
                                    var dataSetCodes = []
                                    for (var i = 0; i < response.result.length; i++) {
                                        dataSetCodes.push(response.result[i].code)
                                    }

                                    // Sort by code
                                    dataSetCodes.sort()

                                    // Store
                                    dataModelObj.dataSetCodes = dataSetCodes;

                                    // Sort and store the datasets as well
                                    dataModelObj.dataSets = []
                                    var unsortedDataSets = response.result;
                                    for (var i = 0; i < dataSetCodes.length; i++) {
                                        for (var j = 0; j < unsortedDataSets.length; j++) {
                                            if (unsortedDataSets[j].code == dataSetCodes[i]) {
                                                // Found. Add it to the datasets and remove it from the unsorted list
                                                dataModelObj.dataSets.push(unsortedDataSets[j]);
                                                unsortedDataSets.splice(j, 1);
                                                break;
                                            }
                                        }
                                    }

                                    // Initialize the experiment view
                                    DATAVIEWER.initView();

                                }
                            }

                        });
                    }

                });

            } else {

                // Could not retrieve the sample object
                dataModelObj.sample = null;
                dataModelObj.expId = null;
                dataModelObj.exp = null;
                dataModelObj.expName = "Error: could not retrieve experiment!";

                // Initialize the experiment view
                DATAVIEWER.initView();

            }
        }

    });

    // File URL
    this.fileURL = [];

}

/**
 * Get all data relative to current sample
 * @param action Function callback.
 */
DataModel.prototype.initData = function(action) {

    // Build the code from the identifier
    this.sampleCode = this.sampleId.substring(1 + this.sampleId.lastIndexOf("/"));

    var searchCriteria = new SearchCriteria();
    searchCriteria.addMatchClause(SearchCriteriaMatchClause.createAttributeMatch("TYPE", "MICROSCOPY_SAMPLE_TYPE"));
    searchCriteria.addMatchClause(SearchCriteriaMatchClause.createAttributeMatch("CODE", this.sampleCode));
    this.openbisServer.searchForSamples(searchCriteria, action);

};

/**
 * Get current experiment.
 * @param {Function} action Function callback
 */
DataModel.prototype.getExperimentData = function(action) {
    // expId must be in an array: [expId]
    this.openbisServer.listExperimentsForIdentifiers([this.expId], action);
};

/**
 * Get datasets for current experiments
 * @param action
 */
DataModel.prototype.getDataSetsForSampleAndExperiment = function(action) {

    // Experiment criteria
    var experimentCriteria =
    {
        targetEntityKind : "EXPERIMENT",
        criteria : {
            matchClauses :
                [ {"@type" : "AttributeMatchClause",
                    "attribute" : "CODE",
                    "fieldType" : "ATTRIBUTE",
                    "desiredValue" : this.exp.code
                } ]
        }
    };

    // Sample criteria
    var sampleCriteria =
    {
        targetEntityKind : "SAMPLE",
        criteria : {
            matchClauses :
                [ {"@type" : "AttributeMatchClause",
                    "attribute" : "CODE",
                    "fieldType" : "ATTRIBUTE",
                    "desiredValue" : this.sampleCode
                } ]
        }
    };

    // Dataset container criteria
    var criteria =
    {
        subCriterias : [ experimentCriteria, sampleCriteria ],
        matchClauses :
            [ {"@type":"AttributeMatchClause",
                attribute : "TYPE",
                fieldType : "ATTRIBUTE",
                desiredValue : "MICROSCOPY_IMG_CONTAINER"
            } ],
        operator : "MATCH_ALL_CLAUSES"
    };

    // Search
    this.openbisServer.searchForDataSets(criteria, action);

}


/**
 * Call an aggregation plug-in to copy the datasets associated to the experiment and sample.
 * @param {type} ?
 * @param {type} ?
 * @param {type} ?
 * @returns {tubes} ?
 */
DataModel.prototype.copyDatasetsToUserDir = function(experimentId, sampleId, mode) {

    // Add call to the aggregation service
    var parameters = {
        experimentId: experimentId,
        sampleId: sampleId,
        mode: mode
    };

    // Inform the user that we are about to process the request
    DATAVIEWER.displayStatus("Please wait while processing your request. This might take a while...", "info");

    // Must use global object
    DATAMODEL.openbisServer.createReportFromAggregationService(CONFIG['dataStoreServer'],
        "export_microscopy_datasets", parameters,
        DATAMODEL.processResultsFromExportDatasetsServerSidePlugin );
};

/**
 * Process the results returned from the copyDatasetsToUserDir() server-side plug-in
 * @param response JSON object
 */
DataModel.prototype.processResultsFromExportDatasetsServerSidePlugin = function (response) {

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
        r_Success = false;

    } else {

        // No obvious error. Retrieve the results
        status = "";
        if (response.result.rows.length != 1) {

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
            if (r_Completed == false) {

                // We only need the UID of the job
                parameters = {};
                parameters["uid"] = r_UID;

                // Call the plug-in
                setTimeout(function() {
                        DATAMODEL.openbisServer.createReportFromAggregationService(
                            CONFIG['dataStoreServer'],
                            "export_microscopy_datasets", parameters,
                            DATAMODEL.processResultsFromExportDatasetsServerSidePlugin)
                    },
                    parseInt(CONFIG['queryPluginStatusInterval']));

                // Return here
                return;

            } else {

                if (row.length != 8) {

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

                    if (r_Success == true) {
                        var snip = "<b>Congratulations!</b>&nbsp;";
                        if (r_NCopiedFiles == 1) {
                            snip = snip +
                                "<span class=\"badge\">1</span> file was ";
                        } else {
                            snip = snip +
                                "<span class=\"badge\">" +
                                r_NCopiedFiles + "</span> files were ";
                        }
                        if (r_Mode == "normal") {
                            status = snip + "successfully exported to " +
                                "{...}/" + r_RelativeExpFolder + ".";
                        } else if (r_Mode == "hrm") {
                            status = snip + "successfully exported to your HRM source folder.";
                        } else {
                            // Add a placeholder to store the download URL.
                            status = snip + "successfully packaged. <span id=\"download_url_span\"></span>";
                        }
                        level = "success";
                    } else {
                        if (r_Mode == "normal") {
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
    if (r_Success == true && r_Mode == "zip") {
        DATAMODEL.openbisServer.createSessionWorkspaceDownloadUrl(r_ZipArchiveFileName,
            function(url) {
                var downloadString =
                    '<img src="img/download.png" />&nbsp;<a href="' + url + '">Download</a>!';
                $("#download_url_span").html(downloadString);
            });
    }
};