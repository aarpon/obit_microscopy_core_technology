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

    // Get the experiment name view
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

    var spOp = "<span class=\"label label-default\">";
    var spCl = "</span>";

    // Display the sample name and code
    var sample_name;
    if (sample.properties.MICROSCOPY_SAMPLE_NAME) {
        sample_name = sample.properties.MICROSCOPY_SAMPLE_NAME;
    } else {
        sample_name = sample.code;
    }
    sampleNameView.append("<h2>" + sample_name + "</h2>");

    // Display the experiment name (code) and link it to the experiment web app
    var link = $("<a>").text(exp.code).attr("href", "#").click(function() {
        window.top.location.hash = "#entity=EXPERIMENT&permId=" + exp.permId +
            "&ui-subtab=webapp-section_microscopy-experiment-viewer";
        return false;
    });

    // Display the experiment name
    detailView.append("<p>" + spOp + "Experiment name" + spCl + "</p>");
    detailView.append($("<p>").append(link));

    // Display the experiment description
    var exp_descr;
    if (exp.properties.MICROSCOPY_EXPERIMENT_DESCRIPTION) {
        exp_descr = exp.properties.MICROSCOPY_EXPERIMENT_DESCRIPTION;
    } else {
        exp_descr = "<i>No description provided.</i>";
    }
    detailView.append(
            "<p>" + spOp + "Experiment description" + spCl + "</p>" +
            "<p>" + exp_descr + "</p>");


    // Display the sample description
    var sample_descr;
    if (sample.properties.MICROSCOPY_SAMPLE_DESCRIPTION) {
        sample_descr = sample.properties.MICROSCOPY_SAMPLE_DESCRIPTION;
    } else {
        sample_descr = "<i>No description provided.</i>";
    }
    detailView.append(
            "<p>" + spOp + "Dataset description" + spCl + "</p>" +
            "<p>" + sample_descr + "</p>");

    // Display the viewer (it will take care of refreshing automatically when
    // the series cahnges, so we do no need to worry about it.
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

    var spOp = "<span class=\"label label-default\">";
    var spCl = "</span>";

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

    // Get the metadata
    var metadata = dataSet.properties.MICROSCOPY_IMG_CONTAINER_METADATA;

    // Get the parameter view
    var paramView = $("#paramView");
    paramView.empty();

    // Use JQuery to parse the metadata XML into an object
    var metadataObj = $.parseXML(metadata);

    // Check whether we found metadata information
    if (! metadataObj.hasChildNodes()) {
        paramView.empty();
        paramView.append("No metadata information found.");
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

    // Display the metadata
    paramView.append(
            "<p>" + spOp + "Dataset/series sizes" + spCl + "</p>" +
            "<table><tbody>" +
                "<tr>" +
                    "<th>X</th><th>Y</th><th>Z</th><th>C</th><th>T</th>" +
                    "<th>vX [&micro;m]</th><th>vY [&micro;m]</th><th>vZ [&micro;m]</th>" +
                "</tr>" +
                "<tr>" +
                    "<td>" + sizeX + "</td><td>" + sizeY + "</td><td>" + sizeZ + "</td>" +
                    "<td>" + sizeC + "</td><td>" + sizeT + "</td>" +
                    "<td>" + sVoxelX + "</td><td>" + sVoxelY + "</td><td>" + sVoxelZ + "</td>" +
                "</tr>" +
            "</tbody></table>");
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

    // Display metadata action
    indx = DATAMODEL.dataSetCodes.indexOf(dataSetCode);
    if (indx != -1) {

        var dataSet = DATAMODEL.dataSets[indx];

        $("#detailViewAction").append(
                "<span><a id=\"view_metadata\" class=\"btn btn-sm btn-success\" " +
                "href=\"#\">" + "<img src=\"img/edit.png\" />&nbsp;" +
                "View/Edit metadata</a></span>&nbsp;");


        // Add link to the metadata view
        $("#view_metadata").click(
            function () {
                window.top.location.hash = "#entity=DATA_SET&permId=" + dataSet.code
                    + "&ui-subtab=managed_property_section_MICROSCOPY_IMG_CONTAINER_METADATA";
                return false;
            });

    }

    // Build and display the call
    callAggregationPlugin = DATAMODEL.copyDatasetsToUserDir;

    // Display the "Export to your folder" button only if enabled in the configuration file
    if (CONFIG['enableExportToUserFolder'] == true) {

        $("#detailViewAction").append(
                "<span><a class=\"btn btn-sm btn-primary\" " +
                "href=\"#\" onclick='callAggregationPlugin(\"" +
                experimentId + "\", \"" + sampleId + "\", \"normal\");  return false;'>" +
                "<img src=\"img/export.png\" />&nbsp;" +
                "Export to your folder</a></span>&nbsp;");
    }

    // Display the "Export to your HRM source folder" button only if enabled in the configuration file
    if (CONFIG['enableExportToHRMSourceFolder'] == true) {

        $("#detailViewAction").append(
                "<span><a class=\"btn btn-sm btn-default\" " +
                "href=\"#\" onclick='callAggregationPlugin(\"" +
                experimentId + "\", \"" + sampleId + "\", \"hrm\");  return false;'>" +
                "<img src=\"img/hrm.png\" />&nbsp;" +
                "Export to your HRM source folder</a></span>&nbsp;");
    }

    // Build and display the call for a zip archive
    $("#detailViewAction").append(
            "<span><a class=\"btn btn-sm btn-primary\" " +
            "href=\"#\" onclick='callAggregationPlugin(\"" +
            experimentId + "\", \"" + sampleId + "\", \"zip\");  return false;'>" +
            "<img src=\"img/zip.png\" />&nbsp;" +
            "Download</a></span>&nbsp;");

};

/**
 * Display status text color-coded by level.
 * @param status: text to be displayed
 * @param level: one of "success", "info", "warning", "error". Default is
 * "info"
 */
DataViewer.prototype.displayStatus = function (status, level) {

    // Display the status
    $("#detailViewStatus").empty();

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
    $("#detailViewStatus").html(status);

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
            var view = widget.getDataSetChooserWidget().getView();

            // Example of how to customize a widget
            view.getDataSetText = function(dataSetCode) {
                indx = DATAMODEL.dataSetCodes.indexOf(dataSetCode)
                return DATAMODEL.dataSets[indx].properties.MICROSCOPY_IMG_CONTAINER_NAME;
            };

            // Example of how to add a change listener to a widget
            widget.getDataSetChooserWidget().addChangeListener(function(event) {
                DATAVIEWER.refreshView(event.getNewValue());
            });
        });

        // Render the component and add it to the page
        $("#imageViewer").empty();
        $("#imageViewer").append(widget.render());

    });

};
