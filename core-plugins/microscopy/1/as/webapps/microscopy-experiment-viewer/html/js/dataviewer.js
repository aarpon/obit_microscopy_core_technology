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
    sampleView = $("#sampleView");
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

        // Put the in a table for now
        sampleView.append("<table><tbody>");
        for (var i = 0; i < samples.length; i++) {
            var name;
            if (samples[i].properties.MICROSCOPY_SAMPLE_NAME) {
                name = samples[i].properties.MICROSCOPY_SAMPLE_NAME;
            } else {
                name = samples[i].code;
            }
            sampleView.append("<tr><td><a href=\"#\">" + name + "</a></td></tr>");
        }
        sampleView.append("</tbody></table>");

        // Display the export action
        this.displayActions(DATAMODEL.exp);

    }

};

/**
 * Build and display the code to trigger the server-side aggregation
 * plugin 'copy_datasets_to_userdir'
 * @param node: DataTree node
 */
DataViewer.prototype.displayActions = function(exp) {

    // Get the detailViewAction div and empty it
    var detailViewAction = $("#detailViewAction");
    detailViewAction.empty();

    // Add actions
    detailViewAction.append(
        "<p><span class=\"label label-warning\">Actions</span></p>");

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
                "<span><a class=\"btn btn-xs btn-primary\" " +
                "href=\"#\" onclick='callAggregationPlugin(\"" +
                experimentId + "\", \"\", \"normal\");'>" +
                "<img src=\"img/export.png\" />&nbsp;" +
                "Export to your folder</a></span>&nbsp;");
    }

    // Build and display the call for a zip archive
    $("#detailViewAction").append(
            "<span><a class=\"btn btn-xs btn-primary\" " +
            "href=\"#\" onclick='callAggregationPlugin(\"" +
            experimentId + "\", \"\", \"zip\");'>" +
            "<img src=\"img/zip.png\" />&nbsp;" +
            "Download</a></span>&nbsp;");

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
