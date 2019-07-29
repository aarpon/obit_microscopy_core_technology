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

}

/**
 * Displays experiment info.
 */
DataViewer.prototype.initView = function() {

    // Div IDs
    var experimentNameView_div, experimentTagView_div,
        experimentDescriptionView_div, experimentAcquisitionDetailsView_div;

    // Aliases
    var samples = DATAMODEL.samples;
    var microscopyExperimentSample = DATAMODEL.microscopyExperimentSample;

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
    if (microscopyExperimentSample.properties["MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME"]) {
        experimentAcquisitionDetailsView_div.append($("<p>").html("This experiment was performed on <b>" +
            microscopyExperimentSample.properties["MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME"] + "</b> and registered on " +
            (new Date(microscopyExperimentSample.registrationDetails.registrationDate)).toDateString() + "."));

    } else {
        experimentAcquisitionDetailsView_div.append($("<p>").html("This experiment was registered on " +
            (new Date(microscopyExperimentSample.registrationDetails.registrationDate)).toDateString() + "."));
    }

    // Get the sample view
    var sampleView_div = $("#sampleView");
    sampleView_div.empty();

    // Make sure we have something to display
    if (microscopyExperimentSample == null) {
        experimentNameView_div.append("<h2>Sorry, could not retrieve information!</h2>");
        experimentNameView_div.append("<p>Please contact your administrator.</p>");
        return;
    }

    // Display the sample name
    experimentNameView_div.append("<h2>" + microscopyExperimentSample.properties.NAME + "</h2>");

    // Display the experiment description
    var exp_descr;
    if (microscopyExperimentSample.properties.MICROSCOPY_EXPERIMENT_DESCRIPTION) {
        exp_descr = microscopyExperimentSample.properties.MICROSCOPY_EXPERIMENT_DESCRIPTION;
    } else {
        exp_descr = "<i>No description provided.</i>";
    }
    experimentDescriptionView_div.append(this.prepareTitle("Description"));
    experimentDescriptionView_div.append($("<p>").html(exp_descr));

    // Get sample tags
    var sampleTags = "<i>None</i>";
    if (microscopyExperimentSample.parents) {
        if (microscopyExperimentSample.parents.length === 0) {
            sampleTags = "<i>None</i>";
        } else {
            var tags = [];
            for (let i = 0; i < microscopyExperimentSample.parents.length; i++) {
                if (microscopyExperimentSample.parents[i].sampleTypeCode === "ORGANIZATION_UNIT") {
                    tags.push(microscopyExperimentSample.parents[i].properties["NAME"]);
                }
            }
            sampleTags = tags.join(", ");
        }
    }
    experimentTagView_div.append(this.prepareTitle("Tags", "info"));
    experimentTagView_div.append($("<p>").html(sampleTags));

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
            if (numSample % 4 === 1) {
                newThumbRow = $("<div />", {class: "row"});
                sampleView_div.append(newThumbRow);
            }

            // Prepare the name to be shown
            var name;
            if (sample.properties["NAME"]) {
                name = sample.properties["NAME"];
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
                    class: "col-md-3",
                    display: "inline",
                    "text-align": "center",
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
                    class: "img-responsive",
                    display: "inline",
                    id: "image_" + sample.code,
                    title: name
                });

            // Build the thumbnail viewer
            thumbnailView.append(thumbnailImage);
            thumbnailView.append($("<br />"));
            thumbnailView.append(link);
            if (datasetSize !== "") {
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
        this.displayActions(DATAMODEL.microscopyExperimentSample);

    }

};

/**
 * Display attachment info and link to the Attachments tab.
 * @param dataModelObj DataMover object.
 * @param attachments: list of attachments
 */
DataViewer.prototype.displayAttachments = function(dataModelObj, attachments) {

    // Get the div
    var experimentAttachmentsViewId = $("#experimentAttachmentsView");

    // Clear the attachment div
    experimentAttachmentsViewId.empty();

    // Text
    var text = "";
    if (dataModelObj.attachments.length === 0) {
        text = "There are no attachments.";
    } else if (dataModelObj.attachments.length === 1) {
        text = "There is one attachment."
    } else {
        text = "There are " + dataModelObj.attachments.length + " attachments.";
    }

    // Link to the data-sets tab
    var link = $("<a>").text(text).attr("href", "#").attr("title", text).click(
        function() {
            var url = "#entity=SAMPLE&permId=" + dataModelObj.microscopyExperimentSample.permId +
                "&ui-subtab=data-sets-section&ui-timestamp=" + (new Date().getTime());
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
 * @param microscopyExperimentSample: Experiment node
 */
DataViewer.prototype.displayActions = function(microscopyExperimentSample) {

    // Get the actionView_div div and empty it
    var actionView_div = $("#actionView");
    actionView_div.empty();
    $("#actionViewExpl").empty();

    // Get the COLLECTION experiment identifier
    var experimentId = microscopyExperimentSample.experimentIdentifierOrNull;

    // Get the MICROSCOPY_EXPERIMENT sample identifier
    var expSamplePermId = microscopyExperimentSample.permId;
    if (undefined === expSamplePermId) {
        DATAVIEWER.displayStatus("Could not retrieve the microscopy experiment identifier!", "error");
        return;
    }

    var img;
    var link;

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
                DATAMODEL.copyDatasetsToUserDir(
                    experimentId, expSamplePermId, "", "normal");
                return false;
            });

        link.prepend(img);

        actionView_div.append(link);
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
                DATAMODEL.copyDatasetsToUserDir(
                    experimentId, expSamplePermId, "", "hrm");
                return false;
            });

        link.prepend(img);

        actionView_div.append(link);

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
            DATAMODEL.copyDatasetsToUserDir(
                experimentId, expSamplePermId, "", "zip");
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
    DATAMODEL.getMicroscopyImgThumbnailDataSetsForMicroscopySample(sample.permId,
        function(dataset) {

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
                    var imD = $("#" + img_id);
                    imD.attr("src", "./img/error.png");
                    imD.attr("title", "Could not find any files associated to this dataset!");

                    return;

                }

                // Find the only fcs file and add its name and URL to the
                // DynaTree
                response.result.forEach(function(f) {

                    if (!f.isDirectory && f.pathInDataSet.toLowerCase() === "thumbnail.png") {

                        // Retrieve the file URL
                        DATAMODEL.openbisServer.getDownloadUrlForFileForDataSetInSession(
                            dataset.code, f.pathInDataSet, function(url){

                                // Replace the image
                                var eUrl = encodeURI(url);
                                eUrl = eUrl.replace('+', '%2B');
                                $("#" + img_id).attr("src", eUrl);
                                $("#" + img_id).css("display", "inline");

                            });
                    } else {

                        // Thumbnail not found!
                        var imD = $("#" + img_id);
                        imD.attr("src", "./img/error.png");
                        imD.attr("title", "Could not find a thumbnail for this dataset!");

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

    var cls;
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
 * @return string: formatted dataset size in the form 322.5 MiB or 3.7 GiB
 */
DataViewer.prototype.formatSizeForDisplay = function(datasetSize) {

    // Output
    var formattedDatasetSize = "";

    // Cast datasetSize to float
    var datasetSizeF = parseFloat(datasetSize);

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
    if (["default", "success", "info", "warning", "danger"].indexOf(level) === -1) {
        level = "default";
    }

    return ($("<p>").append($("<span>").addClass("label").addClass("label-" + level).text(title)));

};
