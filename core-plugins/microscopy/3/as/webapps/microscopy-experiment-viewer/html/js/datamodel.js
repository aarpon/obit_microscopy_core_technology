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

    // MICROSCOPY_EXPERIMENT sample identifier
    this.microscopyExperimentSampleId = this.context.getEntityIdentifier();

    // MICROSCOPY_EXMPERIMENT sample perm id
    this.microscopyExperimentSamplePermId = this.context.getEntityPermId();

    // MICROSCOPY_EXPERIMENT sample type
    this.microscopyExperimentSampleType = this.context.getEntityType();

    // (openBIS) Experiment (collection) identifier
    this.collectionId = null;

    // MICROSCOPY_EXPERIMENT sample (entity returned from the context)
    this.microscopyExperimentSample = null;

    // Samples
    this.samples = null;

    // Alias
    var dataModelObj = this;

    // Get the experiment object for given ID and update the model
    this.getMicroscopyExperimentSampleData(function (response) {

        if (response.hasOwnProperty("error")) {
            // Server returned an error
            dataModelObj.collectionId = null;
            dataModelObj.expName = "Error: could not retrieve experiment!";
        } else {

            // Store the (openBIS) experiment identifier
            dataModelObj.collectionId = response.result[0].experimentIdentifierOrNull;

            // Store the MICROSCOPY_EXPERIMENT sample object
            dataModelObj.microscopyExperimentSample = response.result[0];

            // Store the MICROSCOPY_EXPERIMENT_NAME property
            dataModelObj.expName = dataModelObj.microscopyExperimentSample.properties.MICROSCOPY_EXPERIMENT_NAME;

            // Retrieve and display attachment list
            dataModelObj.retrieveAndDisplayAttachments();

            // Now retrieve the list of datasets for the experiment
            dataModelObj.getMicroscopySamplesForMicroscopyExperimentSample(function (response) {

                if (response.hasOwnProperty("error")) {

                    // Server returned an error
                    DATAVIEWER.displayStatus(response.error.message, "error");

                } else {

                    if (response.result.length === 0) {

                        var msg = "No (sample) datasets found for experiment with code " +
                            dataModelObj.collectionId;
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
 *
 * Please note that from version 3, the MICROSCOPY_EXPERIMENT type is now a sample.
 *
 * @param {Function} action Function callback
 */
DataModel.prototype.getMicroscopyExperimentSampleData = function (action) {

    // Get search criteria for sample with type MICROSCOPY_EXPERIMENT and CODE this.microscopyExperimentSampleId
    var sampleCriteria = new SearchCriteria();
    sampleCriteria.addMatchClause(
        SearchCriteriaMatchClause.createAttributeMatch(
            "PERM_ID", this.microscopyExperimentSamplePermId
        )
    );
    sampleCriteria.addMatchClause(
        SearchCriteriaMatchClause.createAttributeMatch(
            "TYPE", this.microscopyExperimentSampleType
        )
    );

    // Search for datasets
    this.openbisServer.searchForSamplesWithFetchOptions(sampleCriteria,
        ["PROPERTIES", "PARENTS"], action);
};

/**
 * Get MICROSCOPY_SAMPLEs for current MICROSCOPY_EXPERIMENT_SAMPLE.
 * @param action
 */
DataModel.prototype.getMicroscopySamplesForMicroscopyExperimentSample = function (action) {

    // Get search criteria for sample of type MICROSCOPY_EXPERIMENT and CODE this.microscopyExperimentSampleId
    var sampleCriteria = new SearchCriteria();
    sampleCriteria.addMatchClause(
        SearchCriteriaMatchClause.createAttributeMatch(
            "PERM_ID", this.microscopyExperimentSamplePermId
        )
    );
    sampleCriteria.addMatchClause(
        SearchCriteriaMatchClause.createAttributeMatch(
            "TYPE", this.microscopyExperimentSampleType
        )
    );

    // Get search criteria for datasets of type MICROSCOPY_SAMPLE_TYPE
    var childSampleCriteria = new SearchCriteria();
    childSampleCriteria.addMatchClause(
        SearchCriteriaMatchClause.createAttributeMatch(
            "TYPE", "MICROSCOPY_SAMPLE_TYPE"
        )
    );

    // Add sample search criteria as subcriteria
    childSampleCriteria.addSubCriteria(
        SearchSubCriteria.createSampleParentCriteria(sampleCriteria)
    );

    // Search for datasets attached to the sample types and code defined above
    this.openbisServer.searchForSamplesWithFetchOptions(childSampleCriteria,
        ["PROPERTIES", "PARENTS"], action);
};

/**
 * Call an aggregation plug-in to copy the datasets associated to selected
 * node to the user folder.
 * @param experimentId COLLECTION experiment ID
 * @param expSampleId MICROSCOPY_EXPERIMENT sample ID.
 * @param sampleId MICROSCOPY_SAMLE_TYPE sample ID
 * @param mode Mode to be passed to the aggregation service.
 */
DataModel.prototype.copyDatasetsToUserDir = function (experimentId, expSampleId, sampleId, mode) {

    // Add call to the aggregation service
    var parameters = {
        experimentId: experimentId,
        expSampleId: expSampleId,
        sampleId: sampleId,
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

                // First, check if the process is finished or whether it is still running

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
                    '<img src="img/download.png" height="32" width="32" />&nbsp;<a href="' + url + '">Download</a>!';
                $("#download_url_span").html(downloadString);
            });
    }

};

/**
 * Get thumbnail dataset for current sample
 * @param expCode Experiment code.
 * @param sampleCode Sample code.
 * @param action Function callback.
 */
DataModel.prototype.getMicroscopyImgThumbnailDataSetsForMicroscopySample = function (expCode, sampleCode, action) {

    // Experiment criteria (experiment of type "COLLECTION" and code expCode)
    var experimentCriteria = new SearchCriteria();
    experimentCriteria.addMatchClause(
        SearchCriteriaMatchClause.createAttributeMatch(
            "CODE", expCode)
    );
    experimentCriteria.addMatchClause(
        SearchCriteriaMatchClause.createAttributeMatch(
            "TYPE", "COLLECTION")
    );

    // Sample criteria (sample of type "MICROSCOPY_SAMPLE_TYPE" and code sampleCode)
    var sampleCriteria = new SearchCriteria();
    sampleCriteria.addMatchClause(
        SearchCriteriaMatchClause.createAttributeMatch(
            "CODE", sampleCode)
    );
    sampleCriteria.addMatchClause(
        SearchCriteriaMatchClause.createAttributeMatch(
            "TYPE", "MICROSCOPY_SAMPLE_TYPE")
    );

    // Dataset criteria
    var datasetCriteria = new SearchCriteria();
    datasetCriteria.addMatchClause(
        SearchCriteriaMatchClause.createAttributeMatch(
            "TYPE", "MICROSCOPY_IMG_CONTAINER")
    );

    // Add sample and experiment search criteria as subcriteria
    datasetCriteria.addSubCriteria(
        SearchSubCriteria.createSampleCriteria(sampleCriteria)
    );
    datasetCriteria.addSubCriteria(
        SearchSubCriteria.createExperimentCriteria(experimentCriteria)
    );

    // Search
    this.openbisServer.searchForDataSets(datasetCriteria, function (response) {

        // Get the containers
        if (response.error || response.result.length === 0) {
            return null;
        }

        // All MICROSCOPY_IMG_CONTAINER datasets (i.e. a file series) contain a MICROSCOPY_IMG_OVERVIEW
        // and a MICROSCOPY_IMG dataset; one of the series will also contain a MICROSCOPY_IMG_THUMBNAIL,
        // which is what we are looking for here.
        // Even though the MICROSCOPY_IMG_THUMBNAIL is always created for series 0, we cannot guarantee
        // here that series zero will be returned as the first. We quickly scan through the returned
        // results for the MICROSCOPY_IMG_CONTAINER that has three contained datasets.
        // From there we can then quickly retrieve the MICROSCOPY_IMG_THUMBNAIL.
        for (var i = 0; i < response.result.length; i++) {
            var series = response.result[i];
            for (var j = 0; j < series.containedDataSets.length; j++) {
                if (series.containedDataSets[j].dataSetTypeCode === "MICROSCOPY_IMG_THUMBNAIL") {
                    action(series.containedDataSets[j]);
                    return;
                }
            }
        }

        // If nothing was found, pass null to the callback
        //action(null);

    });

};

/**
 * Get, store and display the attachment info
 */
DataModel.prototype.retrieveAndDisplayAttachments = function () {

    // Alias
    var dataModelObj = this;

    // Retrieve the attachments
    this.openbisServer.listDataSetsForSample(this.microscopyExperimentSample, true, function (response) {
        if (response.error) {
            dataModelObj.attachments = [];
            console.log("There was an error retrieving the attachments for current experiment!");
        } else {

            // Make sure all datasets are of the correct type
            var attachments = []
            for (var i = 0; i < response.result.length; i++) {

                var tmp = response.result[i];

                if (tmp.dataSetTypeCode === "ATTACHMENT") {
                    attachments.push(tmp);
                }
            }

            // Store the attachment array
            dataModelObj.attachments = attachments;

            // Display the info
            DATAVIEWER.displayAttachments(dataModelObj);
        }
    });

};



