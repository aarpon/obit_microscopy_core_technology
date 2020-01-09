/**
 * DataModel class
 *
 * @author Aaron Ponti
 *
 */

define(["openbis",
        "as/dto/sample/search/SampleSearchCriteria",
        "as/dto/sample/fetchoptions/SampleFetchOptions",
        "as/dto/service/search/AggregationServiceSearchCriteria",
        "as/dto/service/fetchoptions/AggregationServiceFetchOptions",
        "as/dto/service/execute/AggregationServiceExecutionOptions",
        "js/dataviewer"
    ],
    function(openbis,
             SampleSearchCriteria,
             SampleFetchOptions,
             AggregationServiceSearchCriteria,
             AggregationServiceFetchOptions,
             AggregationServiceExecutionOptions,
             DataViewer) {

    "use strict";

    /**
     * DataModel class
     **/
    let DataModel = function () {

        if (!(this instanceof DataModel)) {
            throw new TypeError("DataModel constructor cannot be called as a function.");
        }

        /*
         * Server-side services
         */
        this.exportDatasetsService = null;

        /**
         * Properties
         */

        // Store a reference to the DataViewer as a global
        // variable for easier reach from callbacks.
        if (! window.DATAVIEWER) {
            window.DATAVIEWER = new DataViewer();
        }
        this.dataViewer = window.DATAVIEWER;

        // Instantiate openBIS V3 API
        this.openbisV3 = new openbis();

        // Current experiment version (unused)
        this.EXPERIMENT_LATEST_VERSION = 2;

        // Use the context to log in
        this.openbisV3.loginFromContext();

        // Retrieve information from the context
        const webappcontext = this.openbisV3.getWebAppContext();

        // MICROSCOPY_EXPERIMENT sample identifier
        this.microscopyExperimentSampleId = webappcontext.getEntityIdentifier();

        // MICROSCOPY_EXPERIMENT sample type
        this.microscopyExperimentSampleType = webappcontext.getEntityType();

        // MICROSCOPY_EXPERIMENT sample (entity returned from the context)
        this.microscopyExperimentSample = null;

        // Samples
        this.samples = null;

        // Retrieve the {...}_EXPERIMENT data with all relevant information
        this.getMicroscopyExperimentSampleDataAndDisplay();

    };

    /**
     * Methods
     */

    DataModel.prototype = {

        constructor: DataModel,

        /**
         * Call an aggregation plug-in to copy the datasets associated to selected
         * node to the user folder.
         * @param experimentId COLLECTION experiment ID
         * @param expSamplePermId MICROSCOPY_EXPERIMENT sample permanent ID.
         * @param samplePermId MICROSCOPY_SAMPLE_TYPE sample permanent ID
         * @param mode Mode to be passed to the aggregation service.
         */
        callServerSidePluginExportDataSets: function (experimentId,
                                                      expSamplePermId,
                                                      samplePermId,
                                                      mode) {

            // Parameters for the aggregation service
            let parameters = {
                experimentId: experimentId,
                expSamplePermId: expSamplePermId,
                samplePermId: samplePermId,
                mode: mode
            };

            // Inform the user that we are about to process the request
            DATAVIEWER.displayStatus("Please wait while processing your request. This might take a while...", "info");

            // Call service
            if (null === this.exportDatasetsService) {
                let criteria = new AggregationServiceSearchCriteria();
                criteria.withName().thatEquals("export_microscopy_datasets");
                let fetchOptions = new AggregationServiceFetchOptions();
                this.openbisV3.searchAggregationServices(criteria, fetchOptions).then(function(result) {
                    if (undefined === result.objects) {
                        console.log("Could not retrieve the server-side aggregation service!")
                        return;
                    }
                    DATAMODEL.exportDatasetsService = result.getObjects()[0];

                    // Now call the service
                    let options = new AggregationServiceExecutionOptions();
                    for (let key in parameters) {
                        options.withParameter(key, parameters[key]);
                    }
                    DATAMODEL.openbisV3.executeAggregationService(
                        DATAMODEL.exportDatasetsService.getPermId(),
                        options).then(function(result) {
                        DATAMODEL.processResultsFromExportDataSetsServerSidePlugin(result);
                    });
                });
            } else {
                // Call the service
                let options = new AggregationServiceExecutionOptions();
                for (let key in parameters) {
                    options.withParameter(key, parameters[key]);
                }
                this.openbisV3.executeAggregationService(
                    this.exportDatasetsService.getPermId(),
                    options).then(function(result) {
                    DATAMODEL.processResultsFromExportDataSetsServerSidePlugin(result);
                });
            }
        },

        /**
         * Get the  MicroscopyExperiment sample and displays via the DataViewer
         */
        getMicroscopyExperimentSampleDataAndDisplay: function() {

            // Search for the sample of type and given perm id
            let criteria = new SampleSearchCriteria();
            criteria.withType().withCode().thatEquals(this.microscopyExperimentSampleType);
            criteria.withIdentifier().thatEquals(this.microscopyExperimentSampleId);
            let fetchOptions = new SampleFetchOptions();
            fetchOptions.withType();
            fetchOptions.withProperties();
            fetchOptions.withDataSets().withType();
            fetchOptions.withExperiment();
            fetchOptions.withExperiment().withType();

            // Children are MICROSCOPY_SAMPLEs; let's not
            // retrieve more than 250.
            let childrenFetchOptions = new SampleFetchOptions();
            childrenFetchOptions.withType();
            childrenFetchOptions.withProperties();
            childrenFetchOptions.from(0);
            childrenFetchOptions.count(250);
            fetchOptions.withChildrenUsing(childrenFetchOptions);

            // Parents are ORGANIZATION_UNITs ("tags")
            let parentFetchOptions = new SampleFetchOptions();
            parentFetchOptions.withType();
            parentFetchOptions.withProperties();
            fetchOptions.withParentsUsing(parentFetchOptions);

            // Keep a reference to this object (for the callback)
            let dataModelObj = this;

            // Query the server
            this.openbisV3.searchSamples(criteria, fetchOptions).done(function (result) {

                // Store the {...}_EXPERIMENT sample object
                dataModelObj.microscopyExperimentSample = result.getObjects()[0];

                // Store the child damples
                dataModelObj.samples = dataModelObj.microscopyExperimentSample.children;

                // Display
                dataModelObj.dataViewer.initView();
            });
        },

        /**
         * Process the results returned from the callServerSidePluginExportDataSets() server-side plug-in
         * @param table Result table
         */
        processResultsFromExportDataSetsServerSidePlugin: function (table) {

            // Did we get the expected result?
            if (!table.rows || table.rows.length !== 1) {
                DATAVIEWER.displayStatus(
                    "There was an error exporting the data!",
                    "danger");
                return;
            }

            // Get the row of results
            let row = table.rows[0];

            // Retrieve the uid
            let r_UID = row[0].value;

            // Is the process completed?
            let r_Completed = row[1].value;

            if (r_Completed === 0) {

                // Call the plug-in
                setTimeout(function () {

                        // We only need the UID of the job
                        let parameters = {};
                        parameters["uid"] = r_UID;

                        // Now call the service
                        let options = new AggregationServiceExecutionOptions();
                        options.withParameter("uid", r_UID);

                        DATAMODEL.openbisV3.executeAggregationService(
                            DATAMODEL.exportDatasetsService.getPermId(),
                            options).then(function (result) {
                            DATAMODEL.processResultsFromExportDataSetsServerSidePlugin(result);
                        })
                    },
                    parseInt(CONFIG['queryPluginStatusInterval']));

                // Return here
                return;

            }

            // The service completed. We can now process the results.

            // Level of the message
            let level = "";

            // Returned parameters
            let r_Success = row[2].value;
            let r_ErrorMessage = row[3].value;
            let r_NCopiedFiles = row[4].value;
            let r_RelativeExpFolder = row[5].value;
            let r_ZipArchiveFileName = row[6].value;
            let r_Mode = row[7].value;

            if (r_Success === 1) {
                let snip = "<b>Congratulations!</b>&nbsp;";
                if (r_NCopiedFiles === 1) {
                    snip = snip + "<span class=\"badge\">1</span> file was ";
                } else {
                    snip = snip + "<span class=\"badge\">" + r_NCopiedFiles + "</span> files were ";
                }
                if (r_Mode === "normal") {
                    status = snip + "successfully exported to {...}/" + r_RelativeExpFolder + ".";
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

            DATAVIEWER.displayStatus(status, level);

            if (r_Success === 1 && r_Mode === "zip") {

                // Build the download URL with a little hack
                DATAMODEL.openbisV3.getDataStoreFacade().createDataSetUpload("dummy").then(function(result) {
                    let url = result.getUrl();
                    let indx = url.indexOf("/datastore_server/store_share_file_upload");
                    if (indx !== -1) {
                        let dssUrl = url.substring(0, indx);
                        let downloadUrl = encodeURI(
                            dssUrl + "/datastore_server/session_workspace_file_download?" +
                            "sessionID=" + DATAMODEL.openbisV3.getWebAppContext().sessionId + "&filePath=" +
                            r_ZipArchiveFileName);

                        let downloadString =
                            '<img src="img/download.png" heigth="32" width="32"/>&nbsp;<a href="' +
                            downloadUrl + '">Download</a>!';
                        $("#download_url_span").html(downloadString);

                    }
                });
            }
        }
    };

    // Return a DataModel object
    return DataModel;

});
