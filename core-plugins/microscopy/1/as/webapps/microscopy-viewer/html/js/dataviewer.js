/**
 * DataViewer class
 *
 * @author Aaron Ponti
 *
 */

/**
 * A viewer to display DataModel entities to the html page.
 */
function DataViewer() {

    "use strict";

};

/**
 * Link to the requested experiment.
 * @param permId Permanent ID of the experiment.
 * @returns {Function} Callback
 */
DataViewer.prototype.linkToExperiment = function(permId) {

    return function() {
        window.top.location.hash = "#entity=EXPERIMENT&permId=" + permId +
            "&ui-subtab=webapp-section_microscopy-experiment-viewer&ui-timestamp=" + (new Date().getTime());
        return false;
    }

};

/**
 * Displays experiment info
 *
 * @param exp openBIS Experiment object
 */
DataViewer.prototype.initView = function() {

    // Div IDs
    var sampleNameView, detailView, imageView;

    // Aliases
    var sample = DATAMODEL.sample;
    var exp = DATAMODEL.exp;
    var dataSetCodes = DATAMODEL.dataSetCodes;

    // Get the sample name view
    sampleNameView = $("#sampleNameView");
    sampleNameView.empty();

    // Get the detail view
    detailView = $("#detailView");
    detailView.empty();

    // Get the image viewer
    imageView = $("#imageViewer");
    imageView.empty();

    // Make sure we have something to display
    if (sample == null || exp == null) {
        sampleNameView.append("<h2>Sorry, could not retrieve information!</h2>");
        sampleNameView.append("<p>Please contact your administrator.</p>");
        return;
    }

    // If the size property exists (this was added later), retrieve it
    var datasetSize = "";
    if (sample.properties.MICROSCOPY_SAMPLE_SIZE_IN_BYTES) {
        datasetSize = DATAVIEWER.formatSizeForDisplay(sample.properties.MICROSCOPY_SAMPLE_SIZE_IN_BYTES);
    }

    // Display the sample name
    var sample_name;
    if (sample.properties.MICROSCOPY_SAMPLE_NAME) {
        sample_name = sample.properties.MICROSCOPY_SAMPLE_NAME;
    } else {
        sample_name = sample.code;
    }
    sampleNameView.append("<h2>" + sample_name + "</h2>");

    /*
     *
     * Link to the experiment
     *
     */

    // Create a row to store the experiment name / link
    var experimentNameRow = $("<div>").addClass("row");

    // Experiment name title
    var expNameTitle = $("<div>").addClass("metadataTitleText").text("Experiment name");
    experimentNameRow.append($("<div>").addClass("metadataTitle").append(expNameTitle));

    // Display the experiment name (code) and link it to the experiment web app
    var link = $("<a>").text(exp.properties.MICROSCOPY_EXPERIMENT_NAME).attr("href", "#").click(
        DATAVIEWER.linkToExperiment(exp.permId)
    );

    // Experiment name/link
    experimentNameRow.append($("<div>").addClass("metadataValue").append(link));

    // Display the experiment name row
    detailView.append(experimentNameRow);

    /*
     *
     * Experiment description
     *
     */

    // Create a row to store the experiment description
    var experimentDescriptionRow = $("<div>").addClass("row");

    // Experiment description title
    var expDescrTitle = $("<div>").addClass("metadataTitleText").text("Experiment description");
    experimentDescriptionRow.append($("<div>").addClass("metadataTitle").append(expDescrTitle));

    // Retrieve the experiment description
    var expDescrValue;
    if (exp.properties.MICROSCOPY_EXPERIMENT_DESCRIPTION) {
        expDescrValue = exp.properties.MICROSCOPY_EXPERIMENT_DESCRIPTION;
    } else {
        expDescrValue = "<i>No description provided.</i>";
    }

    // Experiment description
    experimentDescriptionRow.append($("<div>").addClass("metadataValue").html(expDescrValue));

    // Display the experiment description row
    detailView.append(experimentDescriptionRow);

    /*
     *
     * Dataset size
     *
     */
    if (datasetSize != "") {

        // Create a row to store the dataset size
        var datasetSizeRow = $("<div>").addClass("row");

        // Dataset size title
        var datasetSizeTitle = $("<div>").addClass("metadataTitleText").text("Dataset size");
        datasetSizeRow.append($("<div>").addClass("metadataTitle").append(datasetSizeTitle));

        // Dataset size
        datasetSizeRow.append($("<div>").addClass("metadataValue").text(datasetSize));

        // Display the experiment description row
        detailView.append(datasetSizeRow);
    }

    /*
     *
     * Dataset description
     *
     */

    // Create a row to store the experiment description
    var datasetDescriptionRow = $("<div>").addClass("row");

    // Experiment description title
    var datasetDescrTitle = $("<div>").addClass("metadataTitleText").text("Dataset description");
    datasetDescriptionRow.append($("<div>").addClass("metadataTitle").append(datasetDescrTitle));

    // Retrieve the dataset (sample) description
    var sampleDescrValue;
    if (sample.properties.MICROSCOPY_SAMPLE_DESCRIPTION) {
        sampleDescrValue = sample.properties.MICROSCOPY_SAMPLE_DESCRIPTION;
    } else {
        sampleDescrValue = "<i>No description provided.</i>";
    }

    // Experiment description
    datasetDescriptionRow.append($("<div>").addClass("metadataValue").html(sampleDescrValue));

    // Display the experiment description row
    detailView.append(datasetDescriptionRow);

    /*
     *
     * Render additional views
     *
     */

    // Display the viewer (it will take care of refreshing automatically when
    // the series changes, so we do no need to worry about it.
    this.displayViewer(dataSetCodes);

    // Refresh the series-dependent part of the UI. The same function will be attached
    // to the ChangeListener of the series selector widget, so that the various parts of
    // the UI are updated when the user chooses another series in the file.
    this.refreshView(dataSetCodes[0]);

};

/**
 * Update the view in response to a change in the selected series.
 * @param selectedSeries Index of the selected series.
 */
DataViewer.prototype.refreshView = function(dataSetCode) {

    // Display the metadata (for the first dataset)
    this.displayMetadata(dataSetCode);

    // Display the export action
    this.displayActions(DATAMODEL.exp, DATAMODEL.sample, dataSetCode);

};

/**
 * Display metadata for specified dataset code.
 * @param dataSetCode Data set code for which to display the metadata.
 */
DataViewer.prototype.displayMetadata = function(dataSetCode) {

    // Find data set object with given code
    var dataSet = [];
    for (var i = 0; i < DATAMODEL.dataSetCodes.length; i++) {
        if (DATAMODEL.dataSets[i].code == dataSetCode) {
            dataSet = DATAMODEL.dataSets[i];
            break;
        }
    }

    // Check that the dataset was found
    if (dataSet.length == 0) {
        this.displayStatus("Dataset with code " + dataSetCode + " not found!", "error");
        return;
    }

    // Get the parameter view
    var paramView = $("#paramView");
    paramView.empty();

    // Prepare the divs to display the information
    var metadataTitleRow = $("<div>").addClass("row");

    // Title
    var expDescrTitle = $("<div>").addClass("metadataTitleSeries").text("Current series");
    metadataTitleRow.append($("<div>").addClass("metadataTitle").append(expDescrTitle));
    paramView.append(metadataTitleRow);

    /*
     *
     *  Metadata for current series
     *
     */

    // Get the metadata
    var metadata = dataSet.properties.MICROSCOPY_IMG_CONTAINER_METADATA;

    // Use JQuery to parse the metadata XML into an object
    try {

        // Try parsing
        var metadataObj = $.parseXML(metadata);

    } catch (err) {

        // Create a row to display the error
        var errorRow = $("<div>").addClass("row");

        // Error title
        var errorTitle = $("<div>").addClass("label label-danger").text("Error");
        errorRow.append($("<div>").addClass("metadataTitle").append(errorTitle));

        // Error value
        var errorMsg = "Error retrieving metadata information for current series!";
        errorRow.append($("<div>").addClass("metadataValue").text(errorMsg));

        // Display the error row
        paramView.append(errorRow);

        // Also display standard error
        this.displayStatus(errorMsg, "error");


        return;

    }

    // Check whether we found metadata information
    if (! metadataObj.hasChildNodes()) {

        // Create a row to display the error
        var errorRow = $("<div>").addClass("row");

        // Error title
        var errorTitle = $("<div>").addClass("label label-danger").text("Error");
        errorRow.append($("<div>").addClass("metadataTitle").append(errorTitle));

        // Error value
        var errorMsg = "Error retrieving metadata information for current series!";
        errorRow.append($("<div>").addClass("metadataValue").text(errorMsg));

        // Display the error row
        paramView.append(errorRow);

        // Also display standard error
        this.displayStatus(errorMsg, "error");

        return;
    }

    // Get the metadata for the series and display it
    var seriesMetadata = metadataObj.childNodes[0];
    var sizeX = seriesMetadata.attributes.getNamedItem("sizeX").value;
    var sizeY = seriesMetadata.attributes.getNamedItem("sizeY").value;
    var sizeZ = seriesMetadata.attributes.getNamedItem("sizeZ").value;
    var sizeC = seriesMetadata.attributes.getNamedItem("sizeC").value;
    var sizeT = seriesMetadata.attributes.getNamedItem("sizeT").value;
    var voxelX = seriesMetadata.attributes.getNamedItem("voxelX").value;
    var voxelY = seriesMetadata.attributes.getNamedItem("voxelY").value;
    var voxelZ = seriesMetadata.attributes.getNamedItem("voxelZ").value;

    // Format the metadata
    var sVoxelX = (new Number(voxelX)).toPrecision(2);
    var sVoxelY = (new Number(voxelY)).toPrecision(2);
    var sVoxelZ = (new Number(voxelZ)).toPrecision(2);


    /*
     *
     *  Dataset geometry
     *
     */

    // Create a row to store the dataset geometry
    var datasetGeometryRow = $("<div>").addClass("row");

    // Dataset geometry title
    var datasetGeometryTitle = $("<div>").addClass("metadataTitleText").text("Geometry [XYZ]");
    datasetGeometryRow.append($("<div>").addClass("metadataTitle").append(datasetGeometryTitle));

    // Dataset geometry
    var datasetGeometryValue = "" + sizeX + "x" + sizeY + "x" + sizeZ + ", " + sizeC + " channel" +
        ((sizeC > 1) ? "s" : "") + ", " + sizeT + " timepoint" + ((sizeT > 1) ? "s" : "");
    datasetGeometryRow.append($("<div>").addClass("metadataValue").text(datasetGeometryValue));

    // Display the experiment description row
    paramView.append(datasetGeometryRow);

    /*
     *
     *  Voxel size
     *
     */

    // Create a row to store the voxel size
    var voxelSizeRow = $("<div>").addClass("row");

    // Voxel size title
    var voxelSizeTitle = $("<div>").addClass("metadataTitleText").html("Voxel size [XYZ] (&micro;m)");
    voxelSizeRow.append($("<div>").addClass("metadataTitle").append(voxelSizeTitle));

    // Voxel size
    var voxelSizeValue = "" + sVoxelX + "x" + sVoxelY;
    if (sVoxelZ != "NaN") {
        voxelSizeValue += "x" + sVoxelZ;
    }
    voxelSizeRow.append($("<div>").addClass("metadataValue").text(voxelSizeValue));

    // Display the experiment description row
    paramView.append(voxelSizeRow);

}

/**
 * Build and display the code to trigger the server-side aggregation
 * plugin 'copy_datasets_to_userdir'
 * @param node: DataTree node
 */
DataViewer.prototype.displayActions = function(exp, sample, dataSetCode) {

    // Get the detailViewAction div and empty it
    var detailViewAction = $("#detailViewAction");
    detailViewAction.empty();

    // Get the experiment identifier
    var experimentId = exp.identifier;
    if (undefined === experimentId) {
        DATAVIEWER.displayStatus("Could not retrieve experiment identifier!", "error");
        return;
    }

    // Get the sample identifier
    var sampleId = sample.identifier;

    // Retrieve action div
    var detailViewActionDiv = $("#detailViewAction");

    // Display metadata action
    var indx = DATAMODEL.dataSetCodes.indexOf(dataSetCode);
    if (indx != -1) {

        var dataSet = DATAMODEL.dataSets[indx];

        var img = $("<img>")
            .attr("src", "img/edit.png");

        var link = $("<a>")
            .addClass("btn btn-sm btn-success action")
            .attr("href", "#")
            .html("&nbsp;View metadata")
            .click(function() {
                window.top.location.hash = "#entity=DATA_SET&permId=" + dataSet.code
                    + "&ui-subtab=managed_property_section_MICROSCOPY_IMG_CONTAINER_METADATA&ui-timestamp="
                    + (new Date().getTime());
                return false;
            });

        link.prepend(img);

        detailViewActionDiv.append(link);

    }

    // Build and display the call
    callAggregationPlugin = DATAMODEL.copyDatasetsToUserDir;

    // Display the "Export to your folder" button only if enabled in the configuration file
    if (CONFIG['enableExportToUserFolder'] == true) {

        var img = $("<img>")
            .attr("src", "img/export.png");

        var link = $("<a>")
            .addClass("btn btn-sm btn-primary action")
            .attr("href", "#")
            .html("&nbsp;Export to your folder")
            .click(function() {
                DATAMODEL.copyDatasetsToUserDir(
                    experimentId, sampleId, "normal");
                return false;
            });

        link.prepend(img);

        detailViewActionDiv.append(link);

    }

    // Display the "Export to your HRM source folder" button only if enabled in the configuration file
    if (CONFIG['enableExportToHRMSourceFolder'] == true) {

        var img = $("<img>")
            .attr("src", "img/hrm.png");

        var link = $("<a>")
            .addClass("btn btn-sm btn-default action")
            .attr("href", "#")
            .html("&nbsp;Export to your HRM source folder")
            .click(function() {
                DATAMODEL.copyDatasetsToUserDir(
                    experimentId, sampleId, "hrm");
                return false;
            });

        link.prepend(img);

        detailViewActionDiv.append(link);

    }

    // Build and display the call for a zip archive
    var img = $("<img>")
        .attr("src", "img/zip.png");

    var link = $("<a>")
        .addClass("btn btn-sm btn-primary action")
        .attr("href", "#")
        .html("&nbsp;Download")
        .click(function() {
            DATAMODEL.copyDatasetsToUserDir(
                experimentId, sampleId, "zip");
            return false;
        });

    link.prepend(img);

    detailViewActionDiv.append(link);

};

/**
 * Display status text color-coded by level.
 * @param status: text to be displayed
 * @param level: one of "success", "info", "warning", "error". Default is
 * "info"
 */
DataViewer.prototype.displayStatus = function(status, level) {

    // Get the the statusView div
    var statusView_div = $("#detailViewStatus");

    // Clear the status
    statusView_div.empty();

    // Make sure the status div is visible
    statusView_div.show();

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

};

/**
 * Display the data viewer for a specified list of dataset codes.
 * @param dataSetCodes List of dataset codes to pass on to the ImageViewer.
 */
DataViewer.prototype.displayViewer = function(dataSetCodes) {

    // We need jQuery, openbis-screening and ImageViewerWidget
    require([ "jquery", "openbis-screening", "components/imageviewer/ImageViewerWidget" ], function($, openbis, ImageViewerWidget) {

        // Create the image viewer component for the specific data sets
        var widget = new ImageViewerWidget(DATAMODEL.openbisServer, dataSetCodes);

        // Do the customization once the component is loaded
        widget.addLoadListener(function() {

            widget.getDataSetChooserWidget().then(function(chooser) {

                var view = chooser.getView();

                // Example of how to customize a widget
                view.getDataSetText = function(dataSetCode) {
                    var indx = DATAMODEL.dataSetCodes.indexOf(dataSetCode);
                    return DATAMODEL.dataSets[indx].properties.MICROSCOPY_IMG_CONTAINER_NAME;
                };

            // Add a change listener to a widget
                chooser.addChangeListener(function(event) {
                    DATAVIEWER.refreshView(event.getNewValue());
                });
            });
        });

        // Render the component and add it to the page
        $("#imageViewer").empty();
        $("#imageViewer").append(widget.render());

    });

};

/**
 * Format dataset size for display.
 * @param datasetSize: size in bytes
 * @return string formatted dataset size in the form 322.5 MiB or 3.7 GiB
 */
DataViewer.prototype.formatSizeForDisplay = function(datasetSize) {

    // Output
    var formattedDatasetSize = "";

    // Cast datasetSize to float
    var datasetSizeF = parseFloat(datasetSize)

    var sMB = datasetSizeF / 1024.0 / 1024.0;
    if (sMB < 1024.0) {
        formattedDatasetSize = sMB.toFixed(2) + " MiB";
    } else {
        var sGB = sMB / 1024.0;
        formattedDatasetSize = sGB.toFixed(2) + " GiB";
    }

    return formattedDatasetSize;
};
