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
    detailView.append(
            "<p>" + spOp + "Experiment name" + spCl + "</p>" +
            "<p>" + name + "</p>");

    detailView.append(
            "<p>" + spOp + "Experiment code" + spCl + "</p>" +
            "<p>" + code + "</p>");
};
