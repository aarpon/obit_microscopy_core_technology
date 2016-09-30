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
    var experimentNameView_div, experimentTagView_div,
        experimentDescriptionView_div, experimentAcquisitionDetailsView_div;

    // Aliases
    var samples = DATAMODEL.samples;
    var exp = DATAMODEL.exp;

    // Get the experiment name view
    experimentNameView_div = $("#experimentNameView");
    experimentNameView_div.empty();

    // Clear the tags view
    experimentTagView_div = $("#experimentTagView");
    experimentTagView_div.empty();

    // Clear the description view
    experimentDescriptionView_div = $("#experimentDescriptionView");
    experimentDescriptionView_div.empty();

    // Clear the acquisition detail view
    experimentAcquisitionDetailsView_div = $("#experimentAcquisitionDetailsView");
    experimentAcquisitionDetailsView_div.empty();
    experimentAcquisitionDetailsView_div.append(this.prepareTitle("Acquisition details", "default"));
    if (exp.properties["MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME"]) {
        experimentAcquisitionDetailsView_div.append($("<p>").html("This experiment was performed on <b>" +
            exp.properties["MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME"] + "</b> and registered on " +
            (new Date(exp.registrationDetails.registrationDate)).toDateString() + "."));

    } else {
        experimentAcquisitionDetailsView_div.append($("<p>").html("This experiment was registered on " +
            (new Date(exp.registrationDetails.registrationDate)).toDateString() + "."));
    }

    // Get the sample view
    var sampleView_div = $("#sampleView");
    sampleView_div.empty();

    // Make sure we have something to display
    if (exp == null) {
        experimentNameView_div.append("<h2>Sorry, could not retrieve information!</h2>");
        experimentNameView_div.append("<p>Please contact your administrator.</p>");
        return;
    }

    // Display the sample name
    experimentNameView_div.append("<h2>" + exp.properties.MICROSCOPY_EXPERIMENT_NAME + "</h2>");

    // Display the experiment description
    var exp_descr;
    if (exp.properties.MICROSCOPY_EXPERIMENT_DESCRIPTION) {
        exp_descr = exp.properties.MICROSCOPY_EXPERIMENT_DESCRIPTION;
    } else {
        exp_descr = "<i>No description provided.</i>";
    }
    experimentDescriptionView_div.append(this.prepareTitle("Description"));
    experimentDescriptionView_div.append($("<p>").html(exp_descr));

    // Get metaprojects (tags)
    var metaprojects = "";
    if (exp.metaprojects) {
        if (exp.metaprojects.length == 0) {
            metaprojects = "<i>None</i>";
        } else if (exp.metaprojects.length == 1) {
            metaprojects = exp.metaprojects[0].name;
        } else {
            for (var i = 0; i < exp.metaprojects.length; i++) {
                if (i < (exp.metaprojects.length - 1)) {
                    metaprojects = metaprojects.concat(exp.metaprojects[i].name + ", ");
                } else {
                    metaprojects = metaprojects.concat(exp.metaprojects[i].name);
                }
            }
        }
    }
    experimentTagView_div.append(this.prepareTitle("Tags", "info"));
    experimentTagView_div.append($("<p>").html(metaprojects));

    // Display the samples
    if (samples != null) {

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
                sampleView_div.append(newThumbRow);
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

            // If the size property exists (this was added later), retrieve it and display it as well
            var datasetSize;
            if (sample.properties.MICROSCOPY_SAMPLE_SIZE_IN_BYTES) {
                datasetSize = DATAVIEWER.formatSizeForDisplay(sample.properties.MICROSCOPY_SAMPLE_SIZE_IN_BYTES);
            } else {
                datasetSize = "";
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
            var link = $("<a>").addClass("filename").text(displayName).attr("href", "#").attr("title", name).click(
                function() {
                    window.top.location.hash = "#entity=SAMPLE&permId=" + sample.permId
                        + "&ui-subtab=webapp-section_microscopy-viewer&ui-timestamp=" + (new Date().getTime());
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
            if (datasetSize != "") {
                thumbnailView.append($("<br />"));
                var spanSz =  $("<span>").addClass("filesize").text(datasetSize);
                thumbnailView.append(spanSz);
            }

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
 * Display attachment info and link to the Attachments tab.
 * @param attachments: list of attachments
 */
DataViewer.prototype.displayAttachments = function(dataMoverObj, attachments) {

    // Get the div
    var experimentAttachmentsViewId = $("#experimentAttachmentsView");

    // Clear the attachment div
    experimentAttachmentsViewId.empty();

    // Text
    var text = "";
    if (dataMoverObj.attachments.length == 0) {
        text = "There are no attachments.";
    } else if (dataMoverObj.attachments.length == 1) {
        text = "There is one attachment."
    } else {
        text = "There are " + dataMoverObj.attachments.length + " attachments.";
    }
    // Link to the attachment tab
    var link = $("<a>").text(text).attr("href", "#").attr("title", text).click(
        function() {
            var url = "#entity=EXPERIMENT&permId=" + dataMoverObj.exp.permId +
                "&ui-subtab=attachment-section&ui-timestamp=" + (new Date().getTime());
            window.top.location.hash = url;
            return false;
        });

    experimentAttachmentsViewId.append(this.prepareTitle("Attachments"));

    // Display the link
    experimentAttachmentsViewId.append(link);

};

/**
 * Build and display the code to trigger the server-side aggregation
 * plugin 'copy_datasets_to_userdir'
 * @param exp: Experiment node
 */
DataViewer.prototype.displayActions = function(exp) {

    // Get the actionView_div div and empty it
    var actionView_div = $("#actionView");
    actionView_div.empty();

    // Get the experiment identifier
    var experimentId = exp.identifier;
    if (undefined === experimentId) {
        DATAVIEWER.displayStatus("Could not retrieve experiment identifier!", "error");
        return;
    }

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
                    experimentId, "", "normal");
                return false;
            });

        link.prepend(img);

        actionView_div.append(link);
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
                    experimentId, "", "hrm");
                return false;
            });

        link.prepend(img);

        actionView_div.append(link);

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
                experimentId, "", "zip");
            return false;
        });

    link.prepend(img);

    actionView_div.append(link);

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

                // Make sure that we got some results from the DSS to process
                if (response.error) {

                    // Thumbnail not found!
                    $("#" + img_id).attr("src", "./img/error.png");
                    $("#" + img_id).attr("title", "Could not find any files associated to this dataset!");

                    return;

                }

                // Find the only fcs file and add its name and URL to the
                // DynaTree
                response.result.forEach(function(f) {

                    if (!f.isDirectory && f.pathInDataSet.toLowerCase() == "thumbnail.png") {

                        // Retrieve the file URL
                        DATAMODEL.openbisServer.getDownloadUrlForFileForDataSetInSession(
                            dataset.code, f.pathInDataSet, function(url){

                                // Replace the image
                                var eUrl = encodeURI(url);
                                eUrl = eUrl.replace('+', '%2B');
                                $("#" + img_id).attr("src", eUrl);

                            });
                    } else {

                        // Thumbnail not found!
                        $("#" + img_id).attr("src", "./img/error.png");
                        $("#" + img_id).attr("title", "Could not find a thumbnail for this dataset!");

                    }
                });

            });

    });

};

/**
 * Display status text color-coded by level.
 * @param status: text to be displayed
 * @param level: one of "success", "info", "warning", "error". Default is "info"
 */
DataViewer.prototype.displayStatus = function(status, level) {

    // Get the the statusView div
    var statusView_div = $("#statusView");

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
 * Format dataset size for display.
 * @param datasetSize: size in bytes
 * @return formattedDatasetSize: formatted dataset size in the form 322.5 MiB or 3.7 GiB
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

/**
 * Prepare a title div to be added to the page.
 * @param title Text for the title
 * @param level One of "default", "info", "success", "warning", "danger". Default is "default".
 */
DataViewer.prototype.prepareTitle = function(title, level) {


    // Make sure the level is valid
    if (["default", "success", "info", "warning", "danger"].indexOf(level) == -1) {
        level = "default";
    }

    return ($("<p>").append($("<span>").addClass("label").addClass("label-" + level).text(title)));

};
