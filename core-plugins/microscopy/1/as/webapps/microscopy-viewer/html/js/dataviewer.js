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
DataViewer.prototype.displayExperimentInfo = function(exp) {

    var experimentNameView, detailView, paramView;

    // Get the experiment name view
    experimentNameView = $("#experimentNameView");
    experimentNameView.empty();

    // Get the detail view
    detailView = $("#detailView");
    detailView.empty();

    var spOp = "<span class=\"label label-default\">";
    var spCl = "</span>";

    // Extract experiment name and underline it in code
    var name = "";
    var code = "";
    var indx = exp.code.lastIndexOf("_");
    if (indx != -1) {
        // Make sure we got the 18 random alphanumeric chars
        var suffix = exp.code.substr(indx);
        if (suffix.length == 19) {
            name =  exp.code.substr(0, indx);
            code = "<b>" + name + "</b>" + suffix;
        } else {
            name = code;
        }
    }

    // Store the experiment name
    experimentNameView.append("<h2>" + name + "</h2>");

    // Store the experiment code
    detailView.append(
            "<p>" + spOp + "Experiment code" + spCl + "</p>" +
            "<p>" + code + "</p>");

    // Get the parameter view
    paramView = $("#paramView");
    paramView.empty();

    // Add the parameters (placeholder)
    paramView.append(
        "<p>" + spOp + "Acquisition parameters" + spCl + "</p>"
    );

    // These will be later queried from the experiment
    paramView.append("<p>...</p>");

    // Display the export action
    this.displayExportAction(exp);

    // Display the download action
    //this.displayDownloadAction(node);
};

/**
 * Build and display the code to trigger the server-side aggregation
 * plugin 'copy_datasets_to_userdir'
 * @param node: DataTree node
 */
DataViewer.prototype.displayExportAction = function(exp) {

    // Get the detailViewAction div
    var detailViewAction = $("#detailViewAction");

    // Add actions (placeholder)
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
                experimentId  + "\", \"normal\");'>" +
                "<img src=\"img/export.png\" />&nbsp;" +
                "Export to your folder</a></span>&nbsp;");
    }

    // Build and display the call for a zip archive
    $("#detailViewAction").append(
            "<span><a class=\"btn btn-xs btn-primary\" " +
            "href=\"#\" onclick='callAggregationPlugin(\"" +
            experimentId  + "\", \"zip\");'>" +
            "<img src=\"img/zip.png\" />&nbsp;" +
            "Compress to archive</a></span>&nbsp;");

};

/**
 * Draw the initial root structure. The tree will then be extended
 * dynamically (via lazy loading) using DynaTree methods.
 * @param status: text to be displayed
 * @param level: one of "success", "info", "warning", "error". Default is
 * "info"
 *
 * @param tree DynaTree object
 */
DataViewer.prototype.displayStatus = function(status, level) {

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