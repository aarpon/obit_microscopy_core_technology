/**
 * DataViewer class
 *
 * @author Aaron Ponti
 *
 */

define([], function () {

    "use strict";

    // Constructor
    let DataViewer = function () {

        // Make sure we are using it as a class
        if (!(this instanceof DataViewer)) {
            throw new TypeError("DataViewer constructor cannot be called as a function.");
        }

        // Max number of thumbnails to display (before the pagination is activated)
        this.totalNumberOfThumbnailsPerPage = 100;

        // Current index of the first thumbnail to display
        this.indexOfFirstThumbnail = 0;
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
         * Display the experiment name
         */
        displayExperimentSampleName: function () {

            // Get the experiment name view
            const experimentNameView_div = $("#experimentNameView");
            experimentNameView_div.empty();

            // Make sure we have something to display
            if (DATAMODEL.microscopyExperimentSample == null) {
                experimentNameView_div.append("<h2>Sorry, could not retrieve information!</h2>");
                experimentNameView_div.append("<p>Please contact your administrator.</p>");
                return;
            }

            // Display the sample name
            experimentNameView_div.append("<h2>" + DATAMODEL.microscopyExperimentSample.properties["$NAME"] + "</h2>");
        },

        /**
         * Display the thumbnails
         */
        displayThumbnails: function () {

            // Get the sample view
            const sampleView_div = $("#sampleView");
            sampleView_div.empty();

            // Display the samples
            if (DATAMODEL.samples != null) {

                // Alias
                const dataViewerObj = this;

                // Add a row
                let newThumbRow = $("<div />", {class: "row"});
                sampleView_div.append(newThumbRow);

                // Display samples with a link to their corresponding webapp.
                // Later we will reorganize the layout (when the thumbnails
                // are ready to be retrieved from openBIS).
                let lastPossibleIndex = DATAMODEL.samples.length - 1;
                let indexOfLastThumbnail = dataViewerObj.indexOfFirstThumbnail +
                    dataViewerObj.totalNumberOfThumbnailsPerPage - 1;
                if (indexOfLastThumbnail > lastPossibleIndex) {
                    indexOfLastThumbnail = lastPossibleIndex;
                }
                for (let i = dataViewerObj.indexOfFirstThumbnail; i <= indexOfLastThumbnail; i++) {

                    // Get current sample
                    let sample = DATAMODEL.samples[i];

                    // Prepare the name to be shown
                    let name;
                    if (sample.properties["$NAME"]) {
                        name = sample.properties["$NAME"];
                    } else {
                        name = sample.code;
                    }

                    // Make sure it is not too long
                    let displayName;
                    let l = name.length;
                    if (l > 30) {
                        displayName = name.substring(0, 13) + "..." + name.substring(l - 13);
                    } else {
                        displayName = name;
                    }

                    // If the size property exists (this was added later), retrieve it and display it as well
                    let datasetSize;
                    if (sample.properties["MICROSCOPY_SAMPLE_SIZE_IN_BYTES"]) {
                        datasetSize = DATAVIEWER.formatSizeForDisplay(sample.properties["MICROSCOPY_SAMPLE_SIZE_IN_BYTES"]);
                    } else {
                        datasetSize = "";
                    }

                    // A column to be added to current row that will store all
                    // elements related to current sample
                    let newThumbCol = $("<div />",
                        {
                            class: "col col-sm-6 col-md-3 col-lg-2",
                            display: "inline",
                            "text-align": "center",
                            id: sample.code
                        });

                    // A div element to contain the thumbnail and its info
                    let thumbnailView = $("<div />", {class: "thumbnailView"});

                    // Link to the dataset (sample) viewer.
                    let link = $("<a>").addClass("filename").text(displayName).attr("href", "#").attr("title", name).click(
                        function () {
                            window.top.location.hash = "#entity=SAMPLE&permId=" + sample.permId
                                + "&ui-subtab=webapp-section_microscopy-viewer&ui-timestamp=" + (new Date().getTime());
                            return false;
                        });

                    // Actual thumbnail. Initially we display a place holder. Later,
                    // we will replace it asynchronously.
                    let thumbnailImage = $("<img />",
                        {
                            src: "./img/wait.gif",
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
                        let spanSz = $("<span>").addClass("filesize").text(datasetSize);
                        thumbnailView.append(spanSz);
                    }

                    // Add the thumbnail to the column and the row
                    newThumbCol.append(thumbnailView);
                    newThumbRow.append(newThumbCol);

                    // Now retrieve the link to the thumbnail image asynchronously and update the <img>
                    DATAVIEWER.displayThumbnailForSample(sample, "image_" + sample.code);
                }

                // Display the export action
                this.displayActions(DATAMODEL.microscopyExperimentSample);
            }
        },

        /**
         * Display the experiment description
         */
        displayExperimentDescription: function () {

            // Clear the description view
            const experimentDescriptionView_div = $("#experimentDescriptionView");
            experimentDescriptionView_div.empty();

            if (DATAMODEL.microscopyExperimentSample == null) {
                return;
            }

            // Display the experiment description
            let exp_descr;
            if (DATAMODEL.microscopyExperimentSample.properties["MICROSCOPY_EXPERIMENT_DESCRIPTION"]) {
                exp_descr = DATAMODEL.microscopyExperimentSample.properties["MICROSCOPY_EXPERIMENT_DESCRIPTION"];
            } else {
                exp_descr = "<i>No description provided.</i>";
            }
            experimentDescriptionView_div.append(this.prepareTitle("Description"));
            experimentDescriptionView_div.append($("<p>").html(exp_descr));
        },

        /**
         * Display the acquisition details
         */
        displayAcquisitionDetails: function () {

            // Clear the acquisition detail view
            const experimentAcquisitionDetailsView_div = $("#experimentAcquisitionDetailsView");
            experimentAcquisitionDetailsView_div.empty();

            if (DATAMODEL.microscopyExperimentSample == null) {
                return;
            }

            // Add section title
            experimentAcquisitionDetailsView_div.append(
                this.prepareTitle("Acquisition details", "default")
            );

            if (DATAMODEL.microscopyExperimentSample.properties["MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME"]) {
                experimentAcquisitionDetailsView_div.append(
                    $("<p>")
                        .html("This experiment was performed on <b>" +
                            DATAMODEL.microscopyExperimentSample.properties["MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME"] +
                            "</b> and registered on " +
                            (new Date(DATAMODEL.microscopyExperimentSample.registrationDate)).toDateString() + "."));
            } else {
                experimentAcquisitionDetailsView_div.append(
                    $("<p>")
                        .html("This experiment was registered on " +
                            (new Date(DATAMODEL.microscopyExperimentSample.registrationDate)).toDateString() + "."));
            }
        },

        /**
         * Display attachment info and link to the Attachments tab.
         *
         * @param experimentSample {...}_EXPERIMENT sample.
         */
        displayAttachments: function (experimentSample) {

            // Get the div
            let experimentAttachmentsViewId = $("#experimentAttachmentsView");

            // Clear the attachment div
            experimentAttachmentsViewId.empty();

            // Text
            let text = "";
            let n = 0;
            for (let i = 0; i < experimentSample.dataSets.length; i++) {
                if (experimentSample.dataSets[i].type.code === "ATTACHMENT") {
                    n += 1;
                }
            }
            if (n === 0) {
                text = "There are no attachments.";
            } else if (n === 1) {
                text = "There is one attachment";
            } else {
                text = "There are " + n + " attachments.";
            }

            // Link to the data-sets tab
            let link = $("<a>")
                .text(text)
                .attr("href", "#")
                .attr("title", text)
                .click(
                    function () {
                        let url = "#entity=SAMPLE&permId=" + experimentSample.permId +
                            "&ui-subtab=data-sets-section&ui-timestamp=" + (new Date().getTime());
                        window.top.location.hash = url;
                        return false;
                    });

            experimentAttachmentsViewId.append(this.prepareTitle("Attachments"));

            // Display the link
            experimentAttachmentsViewId.append(link);

        },

        /**
         * Display status text color-coded by level.
         * @param status: text to be displayed
         * @param level: one of "success", "info", "warning", "error". Default is "info"
         */
        displayStatus: function (status, level) {

            // Get the the statusView div
            const statusView_div = $("#statusView");

            // Clear the status
            statusView_div.empty();

            // Make sure the status div is visible
            statusView_div.show();

            let cls;
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
         * Display tags.
         *
         * @param experimentSample {...}_EXPERIMENT sample.
         */
        displayTags: function (experimentSample) {

            // Get the div
            const experimentTagView = $("#experimentTagView");
            experimentTagView.empty();

            // Get sample tags
            let sampleTags = "<i>None</i>";
            if (experimentSample.parents) {
                if (experimentSample.parents.length === 0) {
                    sampleTags = "<i>None</i>";
                } else {
                    let tags = [];
                    for (let i = 0; i < experimentSample.parents.length; i++) {
                        if (experimentSample.parents[i].type.code === "ORGANIZATION_UNIT") {
                            tags.push(experimentSample.parents[i].properties["$NAME"]);
                        }
                    }
                    sampleTags = tags.join(", ");
                }
            }
            experimentTagView.append(this.prepareTitle("Tags", "info"));
            experimentTagView.append($("<p>").html(sampleTags));

        },

        /**
         * Prepare a title div to be added to the page.
         * @param title Text for the title
         * @param level One of "default", "info", "success", "warning", "danger". Default is "default".
         */
        prepareTitle: function (title, level) {

            // Make sure the level is valid
            if (["default", "success", "info", "warning", "danger"].indexOf(level) === -1) {
                level = "default";
            }

            return ($("<p>").append($("<span>").addClass("label").addClass("label-" + level).text(title)));

        },

        /**
         * Format dataset size for display.
         * @param datasetSize: size in bytes
         * @return string: formatted dataset size in the form 322.5 MiB or 3.7 GiB
         */
        formatSizeForDisplay: function (datasetSize) {

            // Output
            let formattedDatasetSize = "";

            // Cast datasetSize to float
            let datasetSizeF = parseFloat(datasetSize);

            let sMB = datasetSizeF / 1024.0 / 1024.0;
            if (sMB < 1024.0) {
                formattedDatasetSize = sMB.toFixed(2) + " MiB";
            } else {
                let sGB = sMB / 1024.0;
                formattedDatasetSize = sGB.toFixed(2) + " GiB";
            }

            return formattedDatasetSize;
        },

        displayThumbnailForSample: function (sample, img_id) {

            require([
                    "as/dto/dataset/search/DataSetSearchCriteria",
                    "as/dto/dataset/fetchoptions/DataSetFetchOptions",
                    "dss/dto/datasetfile/search/DataSetFileSearchCriteria",
                    "dss/dto/datasetfile/fetchoptions/DataSetFileFetchOptions",
                ],

                function (
                    DataSetSearchCriteria,
                    DataSetFetchOptions,
                    DataSetFileSearchCriteria,
                    DataSetFileFetchOptions) {

                    let dataSetCriteria = new DataSetSearchCriteria();
                    dataSetCriteria.withType().withCode().thatEquals("MICROSCOPY_IMG_CONTAINER");
                    dataSetCriteria.withSample().withPermId().thatEquals(sample.permId.permId);

                    let dataSetFetchOptions = new DataSetFetchOptions();
                    dataSetFetchOptions.withChildren();
                    dataSetFetchOptions.withProperties();
                    dataSetFetchOptions.withComponents();
                    dataSetFetchOptions.withComponents().withType();

                    // Query the server
                    DATAMODEL.openbisV3.searchDataSets(dataSetCriteria, dataSetFetchOptions).done(function (result) {
                        if (result.getTotalCount() === 0) {

                            // Thumbnail
                            let imD = $("#" + img_id);

                            // Make sure to reset the display attribute
                            imD.css("display", "inline");

                            // Thumbnail not found!
                            imD.attr("src", "./img/unavailable.png");
                            imD.attr("title", "Could not find a thumbnail for this dataset!");

                            return null;
                        }

                        // Declare the dataSet that we will use to retrieve the thumbnail
                        let dataSet = null;

                        // All MICROSCOPY_IMG_CONTAINER datasets (i.e. a file series) contain a MICROSCOPY_IMG_OVERVIEW
                        // and a MICROSCOPY_IMG dataset; one of the series will also contain a MICROSCOPY_IMG_THUMBNAIL,
                        // which is what we are looking for here.
                        // Even though the MICROSCOPY_IMG_THUMBNAIL is always created for series 0, we cannot guarantee
                        // here that series zero will be returned as the first. We quickly scan through the returned
                        // results for the MICROSCOPY_IMG_CONTAINER that has three contained datasets.
                        // From there we can then quickly retrieve the MICROSCOPY_IMG_THUMBNAIL.
                        external_loop:
                        for (let i = 0; i < result.objects.length; i++) {
                            let currentDataSet = result.objects[i];
                            if (null == currentDataSet.components) {
                                continue;
                            }
                            for (let j = 0; j < currentDataSet.components.length; j++) {
                                if (currentDataSet.components[j].type.code === "MICROSCOPY_IMG_THUMBNAIL") {
                                    dataSet = currentDataSet.components[j];
                                    break external_loop;
                                }
                            }
                        }

                        // Check that we indeed found the dataSet of type MICROSCOPY_IMG_THUMBNAIL
                        if (dataSet == null) {

                            // Thumbnail
                            let imD = $("#" + img_id);

                            // Make sure to reset the display attribute
                            imD.css("display", "inline");

                            // Thumbnail not found!
                            imD.attr("src", "./img/unavailable.png");
                            imD.attr("title", "Could not find a thumbnail for this dataset!");

                            return;
                        }

                        // Now retrieve the thumbnail and add display it

                        // Get the file
                        let criteria = new DataSetFileSearchCriteria();
                        let dataSetCriteria = criteria.withDataSet().withOrOperator();
                        dataSetCriteria.withPermId().thatEquals(dataSet.permId.permId);

                        let fetchOptions = new DataSetFileFetchOptions();

                        // Query the server
                        DATAMODEL.openbisV3.getDataStoreFacade().searchFiles(criteria, fetchOptions).done(function (result) {

                            // Thumbnail
                            let imD = $("#" + img_id);

                            // Make sure to reset the display attribute
                            imD.css("display", "inline");

                            if (result.getTotalCount() === 0) {

                                // Thumbnail not found!
                                imD.attr("src", "./img/unavailable.png");
                                imD.attr("title", "Could not find a thumbnail for this dataset!");

                                return;
                            }

                            // Extract the files
                            let datasetFiles = result.getObjects();

                            // Find the only fcs file and add its name and URL to the DynaTree
                            datasetFiles.forEach(function (f) {

                                if (!f.isDirectory()) {

                                    if (f.getPath() == "thumbnail.png") {
                                        // Build the download URL
                                        let url = f.getDataStore().getDownloadUrl() + "/datastore_server/" +
                                            f.permId.dataSetId.permId + "/" + f.getPath() + "?sessionID=" +
                                            DATAMODEL.openbisV3.getWebAppContext().sessionId;

                                        // Replace the image
                                        let eUrl = encodeURI(url);
                                        eUrl = eUrl.replace('+', '%2B');
                                        imD.attr("src", eUrl);
                                    }
                                }
                            });
                        });
                    });
                });
        },

        /**
         * Build and display the code to trigger the server-side aggregation
         * plugin 'copy_datasets_to_userdir'
         * @param microscopyExperimentSample: Experiment node
         */
        displayActions: function (microscopyExperimentSample) {

            // Get the actionView_div div and empty it
            const actionView_div = $("#actionView");
            actionView_div.empty();
            $("#actionViewExpl").empty();

            // Get the COLLECTION experiment identifier
            let experimentId = microscopyExperimentSample.getExperiment().identifier.identifier;

            // Get the MICROSCOPY_EXPERIMENT sample identifier
            let expSamplePermId = microscopyExperimentSample.permId.permId;
            if (undefined === expSamplePermId) {
                DATAVIEWER.displayStatus("Could not retrieve the microscopy experiment identifier!", "error");
                return;
            }

            let img;
            let link;

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
                    .click(function () {
                        DATAMODEL.callServerSidePluginExportDataSets(
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
                    .click(function () {
                        DATAMODEL.callServerSidePluginExportDataSets(
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
                .click(function () {
                    DATAMODEL.callServerSidePluginExportDataSets(
                        experimentId, expSamplePermId, "", "zip");
                    return false;
                });

            link.prepend(img);

            actionView_div.append(link);

        },

        /**
         * Set up pagination for thumbnails. If there are less thumbnails than the
         * page size, the controls are shown but inactive.
         * @param totalNumberOfSamples Total number of samples in the dataset.
         */
        setUpPagination: function (totalNumberOfSamples) {

            // Get and clear the divs
            const paginationText = $("#paginationText");
            paginationText.empty();
            const paginationView = $("#paginationView");
            paginationView.empty();

            // Calculate the value of the last index
            let lastIndex = this.totalNumberOfThumbnailsPerPage;
            if (lastIndex > DATAMODEL.samples.length) {
                lastIndex = DATAMODEL.samples.length;
            }

            // Set text
            paginationText.text("" +
                (this.indexOfFirstThumbnail + 1) + " - " +
                lastIndex + " of " + totalNumberOfSamples);

            const dataViewerObj = this;

            paginationView.pagination({
                items: totalNumberOfSamples,
                itemsOnPage: this.totalNumberOfThumbnailsPerPage,
                cssStyle: 'compact-theme',
                onPageClick: function (pageNumber, event) {

                    // Calculate the new value of indexOfFirstThumbnail
                    dataViewerObj.indexOfFirstThumbnail = (pageNumber - 1) *
                        dataViewerObj.totalNumberOfThumbnailsPerPage;

                    // Calculate the value of the last index
                    let lastIndex = pageNumber * dataViewerObj.totalNumberOfThumbnailsPerPage;
                    if (lastIndex > DATAMODEL.samples.length) {
                        lastIndex = DATAMODEL.samples.length;
                    }

                    // Set text
                    paginationText.text("" +
                        (dataViewerObj.indexOfFirstThumbnail + 1) + " - " +
                        lastIndex + " of " + totalNumberOfSamples);

                    // Retrieve samples if needed
                    DATAMODEL.retrieveBatchOfSamplesIfNeeded(dataViewerObj.indexOfFirstThumbnail);

                    // Redraw the thumbnails
                    dataViewerObj.displayThumbnails();
                }
            })
        }
    };

    // Return a DataViewer object
    return DataViewer;

});
