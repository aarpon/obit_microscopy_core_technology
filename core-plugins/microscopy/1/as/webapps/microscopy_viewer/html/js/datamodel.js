/**
 * DataModel class
 * 
 * @author Aaron Ponti
 *
 */


/**
 * Define a model class to hold the microscopy data.
 */
function DataModel() {

    "use strict";

    // Create a context object to access the context information
    this.context = new openbisWebAppContext();

    // Create an OpenBIS facade to call JSON RPC services
    this.openbisServer = new openbis("/openbis");
    
    // Reuse the current sessionId that we received in the context for
    // all the facade calls
    this.openbisServer.useSession(this.context.getSessionId());  
    
    // Experiment identifier
    this.expId = this.context.getEntityIdentifier();
    
    // Experiment object and name
    this.exp = null;
    this.expName = "";

    // Alias
    var dataModelObj = this;
    
    // Get the experiment object for given ID and update the model
    this.getExperiment(function(response) {
        
        if (response.hasOwnProperty("error")) {
            // Server returned an error
            dataModelObj.exp = null;
            dataModelObj.expName = "Error: could not retrieve experiment!";
        } else {
            // TODO: Add MICROSCOPY_EXPERIMENT_NAME!
            dataModelObj.exp = response.result[0];
            dataModelObj.expName = dataModelObj.exp.properties.MICROSCOPY_EXPERIMENT_NAME;
        }

        // Display the experiment summary
        DATAVIEWER.displayExperimentInfo(dataModelObj.exp);

    });
}

/**
 * Get the plates for current experiment
 * @param {Function} action Function callback
 * @returns {Array} plates  Array of plates.
 */
DataModel.prototype.getExperiment = function(action) { 
    // expId must be in an array: [expId]
    this.openbisServer.listExperimentsForIdentifiers([this.expId], action);
};
