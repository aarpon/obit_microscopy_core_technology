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
    this.expName = "";

    // Datasets and dataset codes
    this.dataSets = []
    this.dataSetCodes = [];

    // File URL
    this.fileURL = [];

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
            dataModelObj.getDataSetsForExperiment(function(response) {

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
 * Get datasets for current experiments
 * @param action
 */
DataModel.prototype.getDataSetsForExperiment = function(action) {

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

    // Dataset container criteria
    var criteria =
    {
        subCriterias : [ experimentCriteria ],
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
 * Return the series name for the dataset with given code.
 * @param datasetCode Code of the series dataset
 * @returns name of the series.
 */
DataModel.prototype.getSeriesName = function(datasetCode) {
    // TODO: Return the series name
    return datasetCode;
}

/**
 * Call an aggregation plug-in to copy the datasets associated to selected
 * node to the user folder.
 * @param {type} ?
 * @param {type} ?
 * @param {type} ?
 * @returns {tubes} ?
 */
DataModel.prototype.copyDatasetsToUserDir = function(experimentId, mode) {

    // Add call to the aggregation service
    var parameters = {
        experimentId: experimentId,
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