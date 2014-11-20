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

    // Experiment identifier
    this.expId = this.context.getEntityIdentifier();

    // Experiment object and name
    this.exp = null;

    // Samples
    this.samples = null;

    // Alias
    var dataModelObj = this;

    // Get the experiment object for given ID and update the model
    this.getExperimentData(function(response) {

        if (response.hasOwnProperty("error")) {
            // Server returned an error
            dataModelObj.exp = null;
            dataModelObj.expName = "Error: could not retrieve experiment!";
        } else {
            dataModelObj.exp = response.result[0];
            dataModelObj.expName = dataModelObj.exp.properties.MICROSCOPY_EXPERIMENT_NAME;

            // Now retrieve the list of datasets for the experiment
            dataModelObj.getSamplesForExperiment(function(response) {

                if (response.hasOwnProperty("error")) {

                    // Server returned an error
                    DATAVIEWER.displayStatus(response.error.message, "error");

                } else {

                    if (response.result.length == 0) {

                        var msg = "No (sample) datasets found for experiment with code " +
                            dataModelObj.exp.code;
                        DATAVIEWER.displayStatus(msg, "error");

                    } else {

                        // Store the samples
                        dataModelObj.samples = response.result;

                        // Initialize the experiment view
                        DATAVIEWER.initView();

                    }
                }

            });
        }

    });
}

/**
 * Get current experiment.
 * @param {Function} action Function callback
 */
DataModel.prototype.getExperimentData = function(action) {
    // expId must be in an array: [expId]
    this.openbisServer.listExperimentsForIdentifiers([this.expId], action);
};

/**
 * Get samples for current experiment.
 * @param action
 */
DataModel.prototype.getSamplesForExperiment = function(action) {
    // Search
    this.openbisServer.listSamplesForExperiment(this.expId, action);
};

/**
 * Call an aggregation plug-in to copy the datasets associated to selected
 * node to the user folder.
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

    // Get the datastore server name from the configuration
    var dataStoreServer = CONFIG['dataStoreServer'];

    // Inform the user that we are about to process the request
    DATAVIEWER.displayStatus("Please wait while processing your request. This might take a while...", "info");

    // Must use global object
    DATAMODEL.openbisServer.createReportFromAggregationService(dataStoreServer,
        "copy_microscopy_datasets_to_userdir", parameters, function (response) {

            var status;
            var unexpected = "Sorry, unexpected feedback from server " +
                "obtained. Please contact your administrator.";
            var level = "";
            var row;

            // Returned parameters
            var r_Success;
            var r_ErrorMessage;
            var r_NCopiedFiles;
            var r_RelativeExpFolder;
            var r_ZipArchiveFileName;
            var r_Mode;

            if (response.error) {
                status = "Sorry, could not process request.";
                level = "error";
                r_Success = false;
            } else {
                status = "";
                if (response.result.rows.length != 1) {
                    status = unexpected;
                    level = "error";
                } else {
                    row = response.result.rows[0];
                    if (row.length != 6) {
                        status = unexpected;
                        level = "error";
                    } else {

                        // Extract returned values for clarity
                        r_Success = row[0].value;
                        r_ErrorMessage = row[1].value;
                        r_NCopiedFiles = row[2].value;
                        r_RelativeExpFolder = row[3].value;
                        r_ZipArchiveFileName = row[4].value;
                        r_Mode = row[5].value;

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
            DATAVIEWER.displayStatus(status, level);

            // Retrieve the URL (asynchronously)
            if (r_Success == true && r_Mode == "zip")
                DATAMODEL.openbisServer.createSessionWorkspaceDownloadUrl(r_ZipArchiveFileName,
                    function (url) {
                        var downloadString =
                            '<img src="img/download.png" />&nbsp;<a href="' + url + '">Download</a>!';
                        //'<a href="' + url + '"><img src = "img/download.png" />&nbsp;Download</a>';
                        $("#download_url_span").html(downloadString);
                    });
        });

};

/**
 * Get thumbnail dataset for current sample
 * @param action
 */
DataModel.prototype.getDataSetsForSampleAndExperiment = function(expCode, sampleCode, action) {

    // Experiment criteria
    var experimentCriteria =
    {
        targetEntityKind : "EXPERIMENT",
        criteria : {
            matchClauses :
                [ {"@type" : "AttributeMatchClause",
                    "attribute" : "CODE",
                    "fieldType" : "ATTRIBUTE",
                    "desiredValue" : expCode
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
                    "desiredValue" : sampleCode
                } ]
        }
    };

    // Get the thumbnails
    var criteria = {
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
    this.openbisServer.searchForDataSets(criteria, function(response) {

        // Get the containers
        if (response.error || response.result.length == 0) {
            return null;
        }

        // Get the dataset with type MICROSCOPY_IMG_THUMBNAIL from the first series (container)
        // and pass it on to the specified callback function.
        var series = response.result[0];
        for (var i = 0; i < series.containedDataSets.length; i++) {
            if (series.containedDataSets[i].dataSetTypeCode == "MICROSCOPY_IMG_THUMBNAIL") {
                action(series.containedDataSets[i]);
                return;
            }
        }

        // If nothing was found, pass null to the callback
        action(null);

    });

};

