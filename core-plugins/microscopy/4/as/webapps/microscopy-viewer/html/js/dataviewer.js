/**
 * DataViewer class
 *
 * @author Aaron Ponti
 *
 */

define([], function() {

    "use strict";

    // Constructor
    let DataViewer = function () {

        // Make sure we are using it as a class
        if (!(this instanceof DataViewer)) {
            throw new TypeError("DataViewer constructor cannot be called as a function.");
        }
    };

    /**
     * Methods
     */

    DataViewer.prototype = {

        /**
         * Constructor
         */
        constructor: DataViewer,

        /**
         * Build and display the code to trigger the server-side aggregation
         * plugin 'copy_datasets_to_userdir'
         * @param expSample: MICROSCOPY_EXPERIMENT sample object.
         * @param sample MICROSCOPY_SAMPLE object.
         * @param dataSetCode Dataset Code.
         */
        displayActions: function(expSample, sample, dataSetCode) {

            // Get the detailViewAction div and empty it
            const detailViewAction = $("#actionView");
            detailViewAction.empty();
            $("#actionViewExpl").empty();

            // Get the COLLECTION experiment identifier
            let experimentId = sample.experiment.identifier.identifier;
            if (undefined === experimentId) {
                DATAVIEWER.displayStatus("Could not retrieve experiment identifier!", "error");
                return;
            }

            // Get the sample identifier
            let samplePermId = sample.permId.permId;

            // Get the sample experiment identifier
            let expSamplePermId = expSample.permId.permId;

            // Retrieve action div
            const detailViewActionDiv = $("#actionView");

            // Declare some variables
            let img, link;

            // Display the link to the dataset subtab if there are accessory files
            // (of type MICROSCOPY_ACCESSORY_FILE)
            if (DATAMODEL.accessoryFileDatasets.length > 0) {

                img = $("<img>")
                    .attr("src", "img/files.png")
                    .attr("width", 32)
                    .attr("height", 32);

                link = $("<a>")
                    .addClass("action")
                    .attr("href", "#")
                    .attr("title", "")
                    .hover(function () {
                            $("#actionViewExpl").html("View accessory files.");
                        },
                        function () {
                            $("#actionViewExpl").html("");
                        })
                    .html("")
                    .click(function () {
                        window.top.location.hash = "#entity=SAMPLE&permId="
                            + sample.permId
                            + "&ui-subtab=data-sets-section&ui-timestamp="
                            + (new Date().getTime());
                        return false;
                    });

                link.prepend(img);

                detailViewActionDiv.append(link);
            }

            // Display metadata action
            let indx = DATAMODEL.dataSetCodes.indexOf(dataSetCode);
            if (indx !== -1) {

                let dataSet = DATAMODEL.dataSets[indx];

                img = $("<img>")
                    .attr("src", "img/view.png")
                    .attr("width", 32)
                    .attr("height", 32);

                link = $("<a>")
                    .addClass("action")
                    .attr("href", "#")
                    .attr("title", "")
                    .hover(function () {
                            $("#actionViewExpl").html("View metadata.");
                        },
                        function () {
                            $("#actionViewExpl").html("");
                        })
                    .html("")
                    .click(function() {
                        window.top.location.hash = "#entity=DATA_SET&permId="
                            + dataSet.code
                            + "&ui-subtab=managed_property_section_MICROSCOPY_IMG_CONTAINER_METADATA&ui-timestamp="
                            + (new Date().getTime());
                        return false;
                    });

                link.prepend(img);

                detailViewActionDiv.append(link);

            }

            // Display the "Export to your folder" button only if enabled in the configuration file
            if (CONFIG['enableExportToUserFolder'] === true) {

                img = $("<img>")
                    .attr("src", "img/export.png")
                    .attr("width", 32)
                    .attr("height", 32);

                link = $("<a>")
                    .addClass("action")
                    .attr("href", "#")
                    .attr("title", "")
                    .hover(function () {
                            $("#actionViewExpl").html("Export to your folder.");
                        },
                        function () {
                            $("#actionViewExpl").html("");
                        })
                    .html("")
                    .click(function() {
                        DATAMODEL.callServerSidePluginExportDataSets(
                            experimentId, expSamplePermId, samplePermId, "normal");
                        return false;
                    });

                link.prepend(img);

                detailViewActionDiv.append(link);

            }

            // Display the "Export to your HRM source folder" button only if enabled in the configuration file
            if (CONFIG['enableExportToHRMSourceFolder'] === true) {

                img = $("<img>")
                    .attr("src", "img/hrm.png")
                    .attr("width", 32)
                    .attr("height", 32);

                link = $("<a>")
                    .addClass("action")
                    .attr("href", "#")
                    .attr("title", "")
                    .hover(function () {
                            $("#actionViewExpl").html("Export to your HRM source folder.");
                        },
                        function () {
                            $("#actionViewExpl").html("");
                        })
                    .html("")
                    .click(function() {
                        DATAMODEL.callServerSidePluginExportDataSets(
                            experimentId, expSamplePermId, samplePermId, "hrm");
                        return false;
                    });

                link.prepend(img);

                detailViewActionDiv.append(link);

            }

            // Build and display the call for a zip archive
            img = $("<img>")
                .attr("src", "img/zip.png")
                .attr("width", 32)
                .attr("height", 32);

            link = $("<a>")
                .addClass("action")
                .attr("href", "#")
                .attr("title", "")
                .hover(function () {
                        $("#actionViewExpl").html("Download archive.");
                    },
                    function () {
                        $("#actionViewExpl").html("");
                    })
                .html("")
                .click(function() {
                    DATAMODEL.callServerSidePluginExportDataSets(
                        experimentId, expSamplePermId, samplePermId, "zip");
                    return false;
                });

            link.prepend(img);

            detailViewActionDiv.append(link);

        },

        /**
         * Display dataset (physical microscopy file) info
         */
        displayDataSetInfo: function() {

            // Get the dataset view
            const dataSetView = $("#dataSetView");
            dataSetView.empty();

            if (DATAMODEL.microscopySample == null) {
                return;
            }

            // Alias
            const sample = DATAMODEL.microscopySample;

            // If the size property exists (this was added later), retrieve it
            let datasetSize = "";
            if (sample.properties["MICROSCOPY_SAMPLE_SIZE_IN_BYTES"]) {
                datasetSize = DATAVIEWER.formatSizeForDisplay(
                    sample.properties["MICROSCOPY_SAMPLE_SIZE_IN_BYTES"]
                );
            }

            // Dataset size
            if (datasetSize !== "") {

                // Create a row to store the dataset size
                let datasetSizeRow = $("<div>").addClass("row");

                // Dataset size title
                let datasetSizeTitle = $("<div>")
                    .addClass("metadataTitleText")
                    .text("Dataset size");
                datasetSizeRow.append($("<div>")
                    .addClass("metadataTitle")
                    .append(datasetSizeTitle));

                // Dataset size
                datasetSizeRow.append($("<div>")
                    .addClass("metadataValue")
                    .text(datasetSize));

                // Display the experiment description row
                dataSetView.append(datasetSizeRow);
            }

             // Dataset description

            // Create a row to store the experiment description
            let datasetDescriptionRow = $("<div>").addClass("row");

            // Experiment description title
            let datasetDescrTitle = $("<div>")
                .addClass("metadataTitleText")
                .text("Dataset description");
            datasetDescriptionRow.append($("<div>")
                .addClass("metadataTitle")
                .append(datasetDescrTitle));

            // Retrieve the dataset (sample) description
            var sampleDescrValue;
            if (sample.properties["MICROSCOPY_SAMPLE_DESCRIPTION"]) {
                sampleDescrValue = sample.properties["MICROSCOPY_SAMPLE_DESCRIPTION"];
            } else {
                sampleDescrValue = "<i>No description provided.</i>";
            }

            // Experiment description
            datasetDescriptionRow.append($("<div>")
                .addClass("metadataValue")
                .html(sampleDescrValue));

            // Display the experiment description row
            dataSetView.append(datasetDescriptionRow);
        },

        /**
         * Display information concerning the retrieved accessory datasets.
         */
        displayAccessoryDatasets: function() {

            // Get the number of retrieved accessory datasets
            let n = DATAMODEL.accessoryFileDatasets.length;

            // Prepare the text
            let accessoryDatasetsSummary;
            if (n === 0) {
                accessoryDatasetsSummary = "There are no accessory datasets.";
            } else if (n === 1) {
                accessoryDatasetsSummary = "There is one accessory dataset.";
            } else {
                accessoryDatasetsSummary = "There are " + n + " accessory datasets.";
            }

            // Link to the data-sets tab
            let accessoryDatasetsLink = $("<a>")
                .text(accessoryDatasetsSummary)
                .attr("href", "#")
                .attr("title", "These are Data Sets of type 'MICROSCOPY_ACCESSORY_FILE'.")
                .addClass("metadataValue")
                .click(
                    function () {
                        let url = "#entity=SAMPLE&permId=" + DATAMODEL.microscopySamplePermId +
                            "&ui-subtab=data-sets-section&ui-timestamp=" + (new Date().getTime());
                        window.top.location.hash = url;
                        return false;
                    });

            // Get the accessory datasets view
            const accessoryDataSetView = $("#accessoryDataSetView");
            accessoryDataSetView.empty();

            // Create a row to store the accessory datasets info
            let accessoryDataSetRow = $("<div>").addClass("row");

            // Accessory datasets title
            let accessoryDataSetTitle = $("<div>")
                .addClass("metadataTitleText")
                .html("Accessory datasets");
            accessoryDataSetRow.append($("<div>")
                .addClass("metadataTitle")
                .append(accessoryDataSetTitle));

            // Accessory datasets info
            accessoryDataSetRow.append(accessoryDatasetsLink);

            // Display the experiment description row
            accessoryDataSetView.append(accessoryDataSetRow);
        },

        /**
         * Display metadata for specified dataset code.
         * @param dataSetCode Data set code for which to display the metadata.
         */
        displayMetadata: function(dataSetCode) {

            // Find data set object with given code
            let dataSet = [];
            for (let i = 0; i < DATAMODEL.dataSetCodes.length; i++) {
                if (DATAMODEL.dataSets[i].code === dataSetCode) {
                    dataSet = DATAMODEL.dataSets[i];
                    break;
                }
            }

            // Check that the dataset was found
            if (dataSet.length === 0) {
                this.displayStatus("Dataset with code " + dataSetCode + " not found!", "error");
                return;
            }

            // Get the parameter view
            const paramView = $("#paramView");
            paramView.empty();

            // Prepare the divs to display the information
            let metadataTitleRow = $("<div>")
                .addClass("row");

            // Title
            let expDescrTitle = $("<div>")
                .addClass("metadataTitleSeries")
                .text("Current series");
            metadataTitleRow.append($("<div>")
                .addClass("metadataTitle")
                .append(expDescrTitle));
            paramView.append(metadataTitleRow);

            /*
             *
             *  Metadata for current series
             *
             */

            // Get the metadata
            let metadata = dataSet.properties["MICROSCOPY_IMG_CONTAINER_METADATA"];

            // Declare some variables
            let errorRow, errorTitle, errorMsg;

            // Use JQuery to parse the metadata XML into an object
            let metadataObj = null;
            try {

                // Try parsing
                metadataObj = $.parseXML(metadata);

            } catch (err) {

                // Create a row to display the error
                errorRow = $("<div>").addClass("row");

                // Error title
                errorTitle = $("<div>")
                    .addClass("label label-danger")
                    .text("Error");
                errorRow.append($("<div>")
                    .addClass("metadataTitle")
                    .append(errorTitle));

                // Error value
                errorMsg = "Error retrieving metadata information for current series!";
                errorRow.append($("<div>")
                    .addClass("metadataValue")
                    .text(errorMsg));

                // Display the error row
                paramView.append(errorRow);

                // Also display standard error
                this.displayStatus(errorMsg, "error");


                return;

            }

            // Check whether we found metadata information
            if (metadata == null || !metadataObj.hasChildNodes()) {

                // Create a row to display the error
                errorRow = $("<div>").addClass("row");

                // Error title
                errorTitle = $("<div>")
                    .addClass("label label-danger")
                    .text("Error");
                errorRow.append($("<div>")
                    .addClass("metadataTitle")
                    .append(errorTitle));

                // Error value
                errorMsg = "Error retrieving metadata information for current series!";
                errorRow.append($("<div>")
                    .addClass("metadataValue")
                    .text(errorMsg));

                // Display the error row
                paramView.append(errorRow);

                // Also display standard error
                this.displayStatus(errorMsg, "error");

                return;
            }

            // Get the metadata for the series and display it
            let seriesMetadata = metadataObj.childNodes[0];
            let sizeX = seriesMetadata.attributes.getNamedItem("sizeX").value;
            let sizeY = seriesMetadata.attributes.getNamedItem("sizeY").value;
            let sizeZ = seriesMetadata.attributes.getNamedItem("sizeZ").value;
            let sizeC = seriesMetadata.attributes.getNamedItem("sizeC").value;
            let sizeT = seriesMetadata.attributes.getNamedItem("sizeT").value;
            let voxelX = seriesMetadata.attributes.getNamedItem("voxelX").value;
            let voxelY = seriesMetadata.attributes.getNamedItem("voxelY").value;
            let voxelZ = seriesMetadata.attributes.getNamedItem("voxelZ").value;

            // Format the metadata
            let sVoxelX = (Number(voxelX)).toPrecision(2);
            let sVoxelY = (Number(voxelY)).toPrecision(2);
            let sVoxelZ = (Number(voxelZ)).toPrecision(2);

            /*
             *
             *  Dataset geometry
             *
             */

            // Create a row to store the dataset geometry
            const datasetGeometryRow = $("<div>").addClass("row");

            // Dataset geometry title
            let datasetGeometryTitle = $("<div>")
                .addClass("metadataTitleText")
                .text("Geometry [XYZ]");
            datasetGeometryRow.append($("<div>")
                .addClass("metadataTitle")
                .append(datasetGeometryTitle));

            // Dataset geometry
            let datasetGeometryValue = "" + sizeX + "x" + sizeY + "x"
                + sizeZ + ", " + sizeC + " channel"
                + ((sizeC > 1) ? "s" : "") + ", "
                + sizeT + " timepoint" + ((sizeT > 1) ? "s" : "");
            datasetGeometryRow.append($("<div>")
                .addClass("metadataValue")
                .text(datasetGeometryValue));

            // Display the experiment description row
            paramView.append(datasetGeometryRow);

            /*
             *
             *  Voxel size
             *
             */

            // Create a row to store the voxel size
            let voxelSizeRow = $("<div>").addClass("row");

            // Voxel size title
            let voxelSizeTitle = $("<div>")
                .addClass("metadataTitleText")
                .html("Voxel size [XYZ] (&micro;m)");
            voxelSizeRow.append($("<div>")
                .addClass("metadataTitle")
                .append(voxelSizeTitle));

            // Voxel size
            let voxelSizeValue = "" + sVoxelX + "x" + sVoxelY;
            if (sVoxelZ !== "NaN") {
                voxelSizeValue += "x" + sVoxelZ;
            }
            voxelSizeRow.append($("<div>")
                .addClass("metadataValue")
                .text(voxelSizeValue));

            // Display the experiment description row
            paramView.append(voxelSizeRow);

        },

        /**
         * Display the detail view
         */
        displayExperimentInfo: function() {

            // Get the parameter view
            const experimentView = $("#experimentView");
            experimentView.empty();

            // Alias
            const expSample = DATAMODEL.microscopyExperimentSample;

            // Create a row to store the experiment name / link
            var experimentNameRow = $("<div>").addClass("row");

            // Experiment name title
            var expNameTitle = $("<div>")
                .addClass("metadataTitleText")
                .text("Experiment name");
            experimentNameRow.append($("<div>")
                .addClass("metadataTitle")
                .append(expNameTitle));

            // Display the experiment name (code) and link it to the experiment web app
            var link = $("<a>")
                .text(expSample.properties["$NAME"])
                .attr("href", "#")
                .click(
                    DATAVIEWER.linkToExperiment(expSample.permId.permId)
                );

            // Experiment name/link
            experimentNameRow.append($("<div>")
                .addClass("metadataValue")
                .append(link));

            // Display the experiment name row
            experimentView.append(experimentNameRow);

            /*
             *
             * Experiment description
             *
             */

            // Create a row to store the experiment description
            var experimentDescriptionRow = $("<div>").addClass("row");

            // Experiment description title
            var expDescrTitle = $("<div>")
                .addClass("metadataTitleText")
                .text("Experiment description");
            experimentDescriptionRow.append($("<div>")
                .addClass("metadataTitle")
                .append(expDescrTitle));

            // Retrieve the experiment description
            var expDescrValue;
            if (expSample.properties["MICROSCOPY_EXPERIMENT_DESCRIPTION"]) {
                expDescrValue = expSample.properties["MICROSCOPY_EXPERIMENT_DESCRIPTION"];
            } else {
                expDescrValue = "<i>No description provided.</i>";
            }

            // Experiment description
            experimentDescriptionRow.append($("<div>")
                .addClass("metadataValue")
                .html(expDescrValue));

            // Display the experiment description row
            experimentView.append(experimentDescriptionRow);
        },

        /**
         * Display the sample name
         */
        displaySampleName: function() {

            // Get the sample name view
            const sampleNameView = $("#sampleNameView");
            sampleNameView.empty();

            // Make sure we have something to display
            if (DATAMODEL.microscopySample == null) {
                sampleNameView.append($("<h2>").text("Sorry, could not retrieve information!"));
                sampleNameView.append($("<p>").text("Please contact your administrator."));
                return;
            }

            // Display the sample name
            let sample_name;
            if (DATAMODEL.microscopySample.properties["$NAME"]) {
                sample_name = DATAMODEL.microscopySample.properties["$NAME"];
            } else {
                sample_name = DATAMODEL.microscopySample.code;
            }
            sampleNameView.append($("<h2>").text(sample_name));
        },

        /**
         * Display status text color-coded by level.
         * @param status: text to be displayed
         * @param level: one of "success", "info", "warning", "error". Default is
         * "info"
         */
        displayStatus: function (status, level) {

            // Get the the statusView div
            const statusView_div = $("#detailViewStatus");

            // Clear the status
            statusView_div.empty();

            // Make sure the status div is visible
            statusView_div.show();

            let cls = "info";
            switch (level) {
                case "success":
                    cls = "success";
                    break;
                case "info":
                    cls = "info";
                    break;
                case "warning":
                    cls = "warning";
                    break;
                case "error":
                    cls = "danger";
                    break;
                default:
                    cls = "info";
                    break;
            }

            status = "<div class=\"alert alert-" + cls + " alert-dismissable\">" +
                status + "</div>";
            statusView_div.html(status);

        },

        /**
         * Display the data viewer for a specified list of dataset codes.
         * @param dataSetCodes List of dataset codes to pass on to the ImageViewer.
         */
        displayViewer: function(dataSetCodes) {
            require(["openbis-screening",
                    "components/imageviewer/ImageViewerWidget"],
                function (openbis_screening,
                          ImageViewerWidget) {

                const screeningFacade = new openbis_screening(null);
                screeningFacade._internal.sessionToken = DATAMODEL.webappcontext.sessionId;

                // Create the image viewer component for the specific data sets
                const widget = new ImageViewerWidget(screeningFacade, dataSetCodes);

                // Customize the widget
                widget.addLoadListener(function () {

                    widget.getDataSetChooserWidget().then(function (chooser) {

                        const view = chooser.getView();

                        // Show the series name instead of the dataset code
                        view.getDataSetText = function (dataSetCode) {
                            let displayName = dataSetCode;

                            // Return the series name
                            for (let i = 0; i < DATAMODEL.dataSets.length; i++) {
                                if (DATAMODEL.dataSets[i].code === dataSetCode &&
                                    DATAMODEL.dataSets[i].properties["$NAME"]) {
                                    displayName = DATAMODEL.dataSets[i].properties["$NAME"];
                                    break;
                                }
                            }

                            // If not found, return the dataset code
                            return displayName;
                        };

                        // Add a change listener to a widget
                        chooser.addChangeListener(function(event) {
                            DATAVIEWER.refreshView(event.getNewValue());
                        });

                    });
                });

                // Render the component and add it to the page
                const imageViewerDiv = $("#imageViewer");
                imageViewerDiv.empty();
                imageViewerDiv.append(widget.render());
            });
        },

        /**
         * Format dataset size for display.
         * @param datasetSize: size in bytes
         * @return string formatted dataset size in the form 322.5 MiB or 3.7 GiB
         */
        formatSizeForDisplay: function(datasetSize) {

            // Output
            let formattedDatasetSize = "";

            // Cast datasetSize to float
            let datasetSizeF = parseFloat(datasetSize)

            let sMB = datasetSizeF / 1024.0 / 1024.0;
            if (sMB < 1024.0) {
                formattedDatasetSize = sMB.toFixed(2) + " MiB";
            } else {
                var sGB = sMB / 1024.0;
                formattedDatasetSize = sGB.toFixed(2) + " GiB";
            }

            return formattedDatasetSize;
        },

        /**
         * Link to the requested experiment.
         * @param permId Permanent ID of the experiment.
         * @returns {Function} Callback
         */
        linkToExperiment: function(permId) {

            return function() {
                window.top.location.hash = "#entity=SAMPLE&permId="
                    + permId
                    + "&ui-subtab=webapp-section_microscopy-experiment-viewer&ui-timestamp="
                    + (new Date().getTime());
                return false;
            }
        },

         /**
         * Update the view in response to a change in the selected series.
         * @param dataSetCode Dataset code.
         */
        refreshView: function(dataSetCode) {

            // Display the metadata (for the first dataset)
            this.displayMetadata(dataSetCode);

            // Display the export action
            this.displayActions(
                DATAMODEL.microscopyExperimentSample,
                DATAMODEL.microscopySample,
                dataSetCode);
        }

    };

    // Return a DataViewer object
    return DataViewer;
});
