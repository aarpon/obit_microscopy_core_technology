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
    var experimentNameView, detailView;

    // Aliases
    var samples = DATAMODEL.samples;
    var exp = DATAMODEL.exp;

    // Get the experiment name view
    experimentNameView = $("#experimentNameView");
    experimentNameView.empty();

    // Get the detail view
    detailView = $("#detailView");
    detailView.empty();

    // Get the sample view
    var sampleView = $("#sampleView");
    sampleView.empty();

    // Make sure we have something to display
    if (exp == null) {
        experimentNameView.append("<h2>Sorry, could not retrieve information!</h2>");
        experimentNameView.append("<p>Please contact your administrator.</p>");
        return;
    }

    var spOp = "<span class=\"label label-default\">";
    var spCl = "</span>";

    // Display the sample name and code
    experimentNameView.append("<h2>" + exp.code + "</h2>");

    // Display the experiment description
    var exp_descr;
    if (exp.properties.MICROSCOPY_EXPERIMENT_DESCRIPTION) {
        exp_descr = exp.properties.MICROSCOPY_EXPERIMENT_DESCRIPTION;
    } else {
        exp_descr = "<i>No description provided.</i>";
    }
    detailView.append(
            "<p>" + spOp + "Description" + spCl + "</p>" +
            "<p>" + exp_descr + "</p>");


    // Display the samples
    if (samples != null) {

        sampleView.append("<p>" + spOp + "Datasets (samples)" + spCl + "</p>");

        var newThumbRow = null;
        var numSample = 0;

        // Display samples with a link to their corresponding webapp. Later we will reorganize the layout
        // (when the thumbnails are ready to be retrieved from openBIS).
        samples.forEach(function(sample) {

            // Keep track of the number of the sample
            numSample++;

            // Add a new row for the next three thumbnails
            if (numSample % 3 == 1) {
                newThumbRow = $("<div />", {class: "row"});
                sampleView.append(newThumbRow);
            }

            // Prepare the name to be shown
            var name;
            if (sample.properties.MICROSCOPY_SAMPLE_NAME) {
                name = sample.properties.MICROSCOPY_SAMPLE_NAME;
            } else {
                name = sample.code;
            }

            // Make sure it is not too long
            var displayName;
            var l = name.length;
            if (l > 40) {
                displayName = name.substring(0, 18) + "..." + name.substring(l - 18);
            } else {
                displayName = name;
            }

            // A column to be added to current row that will store all
            // elements related to current sample
            var newThumbCol = $("<div />",
                {
                    class: "col-md-4",
                    id : sample.code
                });

            // A div element to contain the thumbnail and its info
            var thumbnailView = $("<div />", { class: "thumbnailView" });

            // Link to the dataset (sample) viewer.
            var link = $("<a>").text(displayName).attr("href", "#").attr("title", name).click(
                function() {
                    window.top.location.hash = "#entity=SAMPLE&permId=" + sample.permId
                        + "&ui-subtab=webapp-section_microscopy-viewer";
                    return false;
                });

            // Actual thumbnail. Initially we display a place holder. Later,
            // we will replace it asynchronously.
            var thumbnailImage = $("<img />",
                {
                    src: "./img/wait.png",
                    id: "image_" + sample.code,
                    title: name
                });

            // Build the thumbnail viewer
            thumbnailView.append(thumbnailImage);
            thumbnailView.append($("<br />"));
            thumbnailView.append(link);

            // Add the thumbnail to the column and the row
            newThumbCol.append(thumbnailView);
            newThumbRow.append(newThumbCol);

            // Now retrieve the link to the thumbnail image asynchronously and update the <img>
            DATAVIEWER.displayThumbnailForSample(sample, "image_" + sample.code);

        });

        // Display the export action
        this.displayActions(DATAMODEL.exp);

    }

};

/**
 * Build and display the code to trigger the server-side aggregation
 * plugin 'copy_datasets_to_userdir'
 * @param exp: Experiment node
 */
DataViewer.prototype.displayActions = function(exp) {

    // Get the detailViewAction div and empty it
    var detailViewAction = $("#detailViewAction");
    detailViewAction.empty();

    // Get the experiment identifier
    var experimentId = exp.identifier;
    if (undefined === experimentId) {
        DATAVIEWER.displayStatus("Could not retrieve experiment identifier!", "error");
        return;
    }

    // Build and display the call
    callAggregationPlugin = DATAMODEL.copyDatasetsToUserDir;

    // Display the "Export to your folder" button only if enabled in the configuration file
    if (CONFIG['enableExportToUserFolder'] == true) {

        $("#detailViewAction").append(
                "<span><a class=\"btn btn-sm btn-primary\" " +
                "href=\"#\" onclick='callAggregationPlugin(\"" +
                experimentId + "\", \"\", \"normal\"); return false;'>" +
                "<img src=\"img/export.png\" />&nbsp;" +
                "Export to your folder</a></span>&nbsp;");
    }

    // Display the "Export to your HRM source folder" button only if enabled in the configuration file
    if (CONFIG['enableExportToHRMSourceFolder'] == true) {

        $("#detailViewAction").append(
                "<span><a class=\"btn btn-sm btn-default\" " +
                "href=\"#\" onclick='callAggregationPlugin(\"" +
                experimentId + "\", \"\", \"hrm\");  return false;'>" +
                "<img src=\"img/hrm.png\" />&nbsp;" +
                "Export to your HRM source folder</a></span>&nbsp;");

    }

    // Build and display the call for a zip archive
    $("#detailViewAction").append(
            "<span><a class=\"btn btn-sm btn-primary\" " +
            "href=\"#\" onclick='callAggregationPlugin(\"" +
            experimentId + "\", \"\", \"zip\"); return false;'>" +
            "<img src=\"img/zip.png\" />&nbsp;" +
            "Download</a></span>&nbsp;");

};

/**
 * Retrieve and display the experiment thumbnails asynchronously
 * @param sample: sample object
 * @param img_id: id of the <img> element to update
 */
DataViewer.prototype.displayThumbnailForSample= function(sample, img_id) {

	// Get the datasets with type "MICROSCOPY_IMG_THUMBNAIL" for current sample
    DATAMODEL.getDataSetsForSampleAndExperiment(DATAMODEL.exp.code, sample.code, function(dataset) {

        // Get the containers
        if (dataset == null) {
            return;
        }

        // Retrieve the file for the dataset and the associated URL
        DATAMODEL.openbisServer.listFilesForDataSet(dataset.code, '/', true,
            function(response) {

                // Find the only fcs file and add its name and URL to the
                // DynaTree
                response.result.forEach(function(f) {

                    if (!f.isDirectory && f.pathInDataSet.toLowerCase() == "thumbnail.png") {

                        // Retrieve the file URL
                        DATAMODEL.openbisServer.getDownloadUrlForFileForDataSetInSession(
                            dataset.code, f.pathInDataSet, function(url){

                                var eUrl = encodeURI(url);
                                eUrl = eUrl.replace('+', '%2B');
                                $("#" + img_id).attr("src", eUrl);
                            });
                    }
                });

            });

    });

};

/**
 * Display status text color-coded by level.
 * @param status: text to be displayed
 * @param level: one of "success", "info", "warning", "error". Default is
 * "info"
 *
 * @param tree DynaTree object
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
