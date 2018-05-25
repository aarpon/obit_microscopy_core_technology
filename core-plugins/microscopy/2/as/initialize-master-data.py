# -*- coding: utf-8 -*-
import ch.systemsx.cisd.openbis.generic.server.jython.api.v1.DataType as DataType

# This code requries openBIS version 18.x and is not compatible with openBIS 16.05
try:

    import ch.systemsx.cisd.openbis.generic.server.CommonServiceProvider as CommonServiceProvider
    import ch.ethz.sis.openbis.generic.asapi.v3.dto.experiment.search.ExperimentTypeSearchCriteria as ExperimentTypeSearchCriteria
    import ch.ethz.sis.openbis.generic.asapi.v3.dto.experiment.fetchoptions.ExperimentTypeFetchOptions as ExperimentTypeFetchOptions
    import ch.ethz.sis.openbis.generic.asapi.v3.dto.experiment.update.ExperimentTypeUpdate as ExperimentTypeUpdate
    import ch.ethz.sis.openbis.generic.asapi.v3.dto.entitytype.id.EntityTypePermId as EntityTypePermId
    import ch.ethz.sis.openbis.generic.asapi.v3.dto.entitytype.EntityKind as EntityKind
    import ch.ethz.sis.openbis.generic.asapi.v3.dto.property.create.PropertyAssignmentCreation as PropertyAssignmentCreation
    import ch.ethz.sis.openbis.generic.asapi.v3.dto.property.id.PropertyTypePermId as PropertyTypePermId


    # Get a session token to be used to update existing properties via the V3 API
    sessionToken = CommonServiceProvider.getCommonServer().tryToAuthenticateAsSystem().getSessionToken()
    v3api = CommonServiceProvider.getApplicationServerApi()

    searchCriteria = ExperimentTypeSearchCriteria()
    searchCriteria.withCode().thatEquals("MICROSCOPY_EXPERIMENT")
    fetchOptions = ExperimentTypeFetchOptions()
    if v3api.searchExperimentTypes(sessionToken, searchCriteria, fetchOptions).getTotalCount() > 0:
        print ("Update: Allowing editing of microscopy experiment names...")
        update = ExperimentTypeUpdate()
        typeId = EntityTypePermId("MICROSCOPY_EXPERIMENT", EntityKind.EXPERIMENT)
        update.setTypeId(typeId)
        assignmentCreation = PropertyAssignmentCreation()
        propertyTypeId = PropertyTypePermId("MICROSCOPY_EXPERIMENT_NAME")
        assignmentCreation.setPropertyTypeId(propertyTypeId)
        assignmentCreation.setShowInEditView(True)
        update.getPropertyAssignments().set(assignmentCreation)
        v3api.updateExperimentTypes(sessionToken, [update])

except:

    print ("Updating the MICROSCOPY_EXPERIMENT_NAME required openBIS 18.x...")


print ("Importing Microscopy Core Technology Master Data...")

tr = service.transaction()

# ==============================================================================
#
# FILE FORMATS
#
# ==============================================================================

# JPG file format
file_type_JPG = tr.getOrCreateNewFileFormatType('JPG')
file_type_JPG.setDescription(None)

# PNG file format
file_type_PNG = tr.getOrCreateNewFileFormatType('PNG')
file_type_PNG.setDescription(None)

# UNKNOWN file format
file_type_UNKNOWN = tr.getOrCreateNewFileFormatType('UNKNOWN')
file_type_UNKNOWN.setDescription('Unknown file format')

# ==============================================================================
#
# MICROSCOPY
#
# ==============================================================================

# MICROSCOPY_EXPERIMENT
exp_type_MICROSCOPY_EXPERIMENT = tr.getOrCreateNewExperimentType('MICROSCOPY_EXPERIMENT')
exp_type_MICROSCOPY_EXPERIMENT.setDescription('Generic microscopy experiment.')

# MICROSCOPY_IMG
data_set_type_MICROSCOPY_IMG = tr.getOrCreateNewDataSetType('MICROSCOPY_IMG')
data_set_type_MICROSCOPY_IMG.setDescription('Generic Microscopy Image.')
if 'setDataSetKind' in dir(data_set_type_MICROSCOPY_IMG):
    data_set_type_MICROSCOPY_IMG.setDataSetKind('PHYSICAL')
data_set_type_MICROSCOPY_IMG.setMainDataSetPattern(None)
data_set_type_MICROSCOPY_IMG.setMainDataSetPath(None)
data_set_type_MICROSCOPY_IMG.setDeletionDisallowed(False)

# MICROSCOPY_IMG_CONTAINER
data_set_type_MICROSCOPY_IMG_CONTAINER = tr.getOrCreateNewDataSetType('MICROSCOPY_IMG_CONTAINER')
data_set_type_MICROSCOPY_IMG_CONTAINER.setDescription('Generic Microscopy Image Container.')
if 'setDataSetKind' in dir(data_set_type_MICROSCOPY_IMG_CONTAINER):
    data_set_type_MICROSCOPY_IMG_CONTAINER.setDataSetKind('CONTAINER')
data_set_type_MICROSCOPY_IMG_CONTAINER.setMainDataSetPattern(None)
data_set_type_MICROSCOPY_IMG_CONTAINER.setMainDataSetPath(None)
data_set_type_MICROSCOPY_IMG_CONTAINER.setDeletionDisallowed(False)

# MICROSCOPY_IMG_OVERVIEW
data_set_type_MICROSCOPY_IMG_OVERVIEW = tr.getOrCreateNewDataSetType('MICROSCOPY_IMG_OVERVIEW')
data_set_type_MICROSCOPY_IMG_OVERVIEW.setDescription('Overview Microscopy Images. Generated from raw images.')
if 'setDataSetKind' in dir(data_set_type_MICROSCOPY_IMG_OVERVIEW):
    data_set_type_MICROSCOPY_IMG_OVERVIEW.setDataSetKind('PHYSICAL')
data_set_type_MICROSCOPY_IMG_OVERVIEW.setMainDataSetPattern(None)
data_set_type_MICROSCOPY_IMG_OVERVIEW.setMainDataSetPath(None)
data_set_type_MICROSCOPY_IMG_OVERVIEW.setDeletionDisallowed(False)

# MICROSCOPY_IMG_THUMBNAIL
data_set_type_MICROSCOPY_IMG_THUMBNAIL = tr.getOrCreateNewDataSetType('MICROSCOPY_IMG_THUMBNAIL')
data_set_type_MICROSCOPY_IMG_THUMBNAIL.setDescription('Representative image for the whole dataset.')
if 'setDataSetKind' in dir(data_set_type_MICROSCOPY_IMG_THUMBNAIL):
    data_set_type_MICROSCOPY_IMG_THUMBNAIL.setDataSetKind('PHYSICAL')
data_set_type_MICROSCOPY_IMG_THUMBNAIL.setMainDataSetPattern(None)
data_set_type_MICROSCOPY_IMG_THUMBNAIL.setMainDataSetPath(None)
data_set_type_MICROSCOPY_IMG_THUMBNAIL.setDeletionDisallowed(False)

# MICROSCOPY_SAMPLE_TYPE
samp_type_MICROSCOPY_SAMPLE_TYPE = tr.getOrCreateNewSampleType('MICROSCOPY_SAMPLE_TYPE')
samp_type_MICROSCOPY_SAMPLE_TYPE.setDescription('Sample type for microscopy data sets.')
samp_type_MICROSCOPY_SAMPLE_TYPE.setListable(True)
samp_type_MICROSCOPY_SAMPLE_TYPE.setShowContainer(False)
samp_type_MICROSCOPY_SAMPLE_TYPE.setShowParents(True)
samp_type_MICROSCOPY_SAMPLE_TYPE.setSubcodeUnique(False)
samp_type_MICROSCOPY_SAMPLE_TYPE.setAutoGeneratedCode(True)
samp_type_MICROSCOPY_SAMPLE_TYPE.setShowParentMetadata(False)
samp_type_MICROSCOPY_SAMPLE_TYPE.setGeneratedCodePrefix('M')

# RESOLUTION (for MICROSCOPY_IMG_OVERVIEW)
prop_type_RESOLUTION = tr.getOrCreateNewPropertyType('RESOLUTION', DataType.VARCHAR)
prop_type_RESOLUTION.setLabel('Resolution')
prop_type_RESOLUTION.setManagedInternally(False)
prop_type_RESOLUTION.setInternalNamespace(True)

# MICROSCOPY_EXPERIMENT_NAME
prop_type_MICROSCOPY_EXPERIMENT_NAME = tr.getOrCreateNewPropertyType('MICROSCOPY_EXPERIMENT_NAME', DataType.VARCHAR)
prop_type_MICROSCOPY_EXPERIMENT_NAME.setLabel('Experiment name')
prop_type_MICROSCOPY_EXPERIMENT_NAME.setManagedInternally(False)
prop_type_MICROSCOPY_EXPERIMENT_NAME.setInternalNamespace(False)

# MICROSCOPY_EXPERIMENT_DESCRIPTION
prop_type_MICROSCOPY_EXPERIMENT_DESCRIPTION = tr.getOrCreateNewPropertyType('MICROSCOPY_EXPERIMENT_DESCRIPTION', DataType.MULTILINE_VARCHAR)
prop_type_MICROSCOPY_EXPERIMENT_DESCRIPTION.setLabel('Description')
prop_type_MICROSCOPY_EXPERIMENT_DESCRIPTION.setManagedInternally(False)
prop_type_MICROSCOPY_EXPERIMENT_DESCRIPTION.setInternalNamespace(False)

# MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME
prop_type_MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME = tr.getOrCreateNewPropertyType('MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME', DataType.VARCHAR)
prop_type_MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME.setLabel('Acquisition station name')
prop_type_MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME.setManagedInternally(False)
prop_type_MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME.setInternalNamespace(False)

# MICROSCOPY_IMG_CONTAINER_METADATA
prop_type_MICROSCOPY_IMG_CONTAINER_METADATA = tr.getOrCreateNewPropertyType('MICROSCOPY_IMG_CONTAINER_METADATA', DataType.XML)
prop_type_MICROSCOPY_IMG_CONTAINER_METADATA.setLabel('Series metadata')
prop_type_MICROSCOPY_IMG_CONTAINER_METADATA.setManagedInternally(False)
prop_type_MICROSCOPY_IMG_CONTAINER_METADATA.setInternalNamespace(False)

# MICROSCOPY_IMG_CONTAINER_NAME
prop_type_MICROSCOPY_IMG_CONTAINER_NAME = tr.getOrCreateNewPropertyType('MICROSCOPY_IMG_CONTAINER_NAME', DataType.VARCHAR)
prop_type_MICROSCOPY_IMG_CONTAINER_NAME.setLabel('Series name')
prop_type_MICROSCOPY_IMG_CONTAINER_NAME.setManagedInternally(False)
prop_type_MICROSCOPY_IMG_CONTAINER_NAME.setInternalNamespace(False)

# MICROSCOPY_SAMPLE_NAME
prop_type_MICROSCOPY_SAMPLE_NAME = tr.getOrCreateNewPropertyType('MICROSCOPY_SAMPLE_NAME', DataType.VARCHAR)
prop_type_MICROSCOPY_SAMPLE_NAME.setLabel('Name')
prop_type_MICROSCOPY_SAMPLE_NAME.setManagedInternally(False)
prop_type_MICROSCOPY_SAMPLE_NAME.setInternalNamespace(False)

# MICROSCOPY_SAMPLE_DESCRIPTION
prop_type_MICROSCOPY_SAMPLE_DESCRIPTION = tr.getOrCreateNewPropertyType('MICROSCOPY_SAMPLE_DESCRIPTION', DataType.MULTILINE_VARCHAR)
prop_type_MICROSCOPY_SAMPLE_DESCRIPTION.setLabel('Description')
prop_type_MICROSCOPY_SAMPLE_DESCRIPTION.setManagedInternally(False)
prop_type_MICROSCOPY_SAMPLE_DESCRIPTION.setInternalNamespace(False)

# MICROSCOPY_SAMPLE_SIZE_IN_BYTES
prop_type_MICROSCOPY_SAMPLE_SIZE_IN_BYTES = tr.getOrCreateNewPropertyType('MICROSCOPY_SAMPLE_SIZE_IN_BYTES',  DataType.INTEGER)
prop_type_MICROSCOPY_SAMPLE_SIZE_IN_BYTES.setLabel('Size')
prop_type_MICROSCOPY_SAMPLE_SIZE_IN_BYTES.setManagedInternally(False)
prop_type_MICROSCOPY_SAMPLE_SIZE_IN_BYTES.setInternalNamespace(False)

# MICROSCOPY_EXPERIMENT_VERSION
prop_type_MICROSCOPY_EXPERIMENT_VERSION = tr.getOrCreateNewPropertyType('MICROSCOPY_EXPERIMENT_VERSION', DataType.INTEGER)
prop_type_MICROSCOPY_EXPERIMENT_VERSION.setLabel('Version')
prop_type_MICROSCOPY_EXPERIMENT_VERSION.setManagedInternally(False)
prop_type_MICROSCOPY_EXPERIMENT_VERSION.setInternalNamespace(False)

# SCRIPTS

# MICROSCOPY_SERIES_METADATA_EDITOR
script_MICROSCOPY_SERIES_METADATA_EDITOR = tr.getOrCreateNewScript('MICROSCOPY_SERIES_METADATA_EDITOR')
script_MICROSCOPY_SERIES_METADATA_EDITOR.setName('MICROSCOPY_SERIES_METADATA_EDITOR')
script_MICROSCOPY_SERIES_METADATA_EDITOR.setDescription('Plug-in for viewing and editing microscopy series metadata information.')
script_MICROSCOPY_SERIES_METADATA_EDITOR.setScript('''import xml.etree.ElementTree as ET

def configureUI():

    # Create a table builder
    tableBuilder = createTableBuilder()

    try:

        # Get the property value and create an XML tree
        root = ET.fromstring(property.getValue().encode('UTF-8'))

        # Extract and sort the metadata attributes
        keys = root.attrib.keys()
        keys.sort()

        # Create the header
        for key in keys: 
            tableBuilder.addHeader(key)

        # Fill in the values
        row = tableBuilder.addRow()
        for key in keys:
            row.setCell(key, root.attrib[key])

    except Exception:

        # Report an error
        tableBuilder.addHeader("Error")
        row = tableBuilder.addRow()
        row.setCell("Error", "Could not retrieve metadata information.")

    # Return the table
    property.setOwnTab(True)
    uiDesc = property.getUiDescription()
    uiDesc.useTableOutput(tableBuilder.getTableModel())
''')
script_MICROSCOPY_SERIES_METADATA_EDITOR.setEntityForScript('DATA_SET')
script_MICROSCOPY_SERIES_METADATA_EDITOR.setScriptType('MANAGED_PROPERTY')

# ASSIGNMENTS
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_NAME = tr.assignPropertyType(exp_type_MICROSCOPY_EXPERIMENT, prop_type_MICROSCOPY_EXPERIMENT_NAME)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_NAME.setMandatory(False)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_NAME.setSection(None)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_NAME.setPositionInForms(1)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_NAME.setShownEdit(False)

assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_DESCRIPTION = tr.assignPropertyType(exp_type_MICROSCOPY_EXPERIMENT, prop_type_MICROSCOPY_EXPERIMENT_DESCRIPTION)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_DESCRIPTION.setMandatory(False)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_DESCRIPTION.setSection(None)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_DESCRIPTION.setPositionInForms(2)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_DESCRIPTION.setShownEdit(True)

assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME = tr.assignPropertyType(exp_type_MICROSCOPY_EXPERIMENT, prop_type_MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME.setMandatory(False)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME.setSection(None)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME.setPositionInForms(4)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_ACQ_HARDWARE_FRIENDLY_NAME.setShownEdit(True)

assignment_DATA_SET_MICROSCOPY_IMG_OVERVIEW_RESOLUTION = tr.assignPropertyType(data_set_type_MICROSCOPY_IMG_OVERVIEW, prop_type_RESOLUTION)
assignment_DATA_SET_MICROSCOPY_IMG_OVERVIEW_RESOLUTION.setMandatory(False)
assignment_DATA_SET_MICROSCOPY_IMG_OVERVIEW_RESOLUTION.setSection(None)
assignment_DATA_SET_MICROSCOPY_IMG_OVERVIEW_RESOLUTION.setPositionInForms(3)
assignment_DATA_SET_MICROSCOPY_IMG_OVERVIEW_RESOLUTION.setShownEdit(True)

assignment_DATA_SET_MICROSCOPY_IMG_CONTAINER_MICROSCOPY_IMG_CONTAINER_METADATA = tr.assignPropertyType(data_set_type_MICROSCOPY_IMG_CONTAINER, prop_type_MICROSCOPY_IMG_CONTAINER_METADATA)
assignment_DATA_SET_MICROSCOPY_IMG_CONTAINER_MICROSCOPY_IMG_CONTAINER_METADATA.setMandatory(False)
assignment_DATA_SET_MICROSCOPY_IMG_CONTAINER_MICROSCOPY_IMG_CONTAINER_METADATA.setSection(None)
assignment_DATA_SET_MICROSCOPY_IMG_CONTAINER_MICROSCOPY_IMG_CONTAINER_METADATA.setPositionInForms(1)
assignment_DATA_SET_MICROSCOPY_IMG_CONTAINER_MICROSCOPY_IMG_CONTAINER_METADATA.setScriptName('MICROSCOPY_SERIES_METADATA_EDITOR')
assignment_DATA_SET_MICROSCOPY_IMG_CONTAINER_MICROSCOPY_IMG_CONTAINER_METADATA.setDynamic(False)
assignment_DATA_SET_MICROSCOPY_IMG_CONTAINER_MICROSCOPY_IMG_CONTAINER_METADATA.setManaged(True)
assignment_DATA_SET_MICROSCOPY_IMG_CONTAINER_MICROSCOPY_IMG_CONTAINER_METADATA.setShownEdit(True)

assignment_DATA_SET_MICROSCOPY_IMG_CONTAINER_MICROSCOPY_IMG_CONTAINER_NAME = tr.assignPropertyType(data_set_type_MICROSCOPY_IMG_CONTAINER, prop_type_MICROSCOPY_IMG_CONTAINER_NAME)
assignment_DATA_SET_MICROSCOPY_IMG_CONTAINER_MICROSCOPY_IMG_CONTAINER_NAME.setMandatory(True)
assignment_DATA_SET_MICROSCOPY_IMG_CONTAINER_MICROSCOPY_IMG_CONTAINER_NAME.setSection(None)
assignment_DATA_SET_MICROSCOPY_IMG_CONTAINER_MICROSCOPY_IMG_CONTAINER_NAME.setPositionInForms(2)
assignment_DATA_SET_MICROSCOPY_IMG_CONTAINER_MICROSCOPY_IMG_CONTAINER_NAME.setShownEdit(False)

assignment_SAMPLE_MICROSCOPY_SAMPLE_TYPE_MICROSCOPY_SAMPLE_NAME = tr.assignPropertyType(samp_type_MICROSCOPY_SAMPLE_TYPE, prop_type_MICROSCOPY_SAMPLE_NAME)
assignment_SAMPLE_MICROSCOPY_SAMPLE_TYPE_MICROSCOPY_SAMPLE_NAME.setMandatory(False)
assignment_SAMPLE_MICROSCOPY_SAMPLE_TYPE_MICROSCOPY_SAMPLE_NAME.setSection(None)
assignment_SAMPLE_MICROSCOPY_SAMPLE_TYPE_MICROSCOPY_SAMPLE_NAME.setPositionInForms(1)
assignment_SAMPLE_MICROSCOPY_SAMPLE_TYPE_MICROSCOPY_SAMPLE_NAME.setShownEdit(False)

assignment_SAMPLE_MICROSCOPY_SAMPLE_TYPE_MICROSCOPY_SAMPLE_DESCRIPTION = tr.assignPropertyType(samp_type_MICROSCOPY_SAMPLE_TYPE, prop_type_MICROSCOPY_SAMPLE_DESCRIPTION)
assignment_SAMPLE_MICROSCOPY_SAMPLE_TYPE_MICROSCOPY_SAMPLE_DESCRIPTION.setMandatory(False)
assignment_SAMPLE_MICROSCOPY_SAMPLE_TYPE_MICROSCOPY_SAMPLE_DESCRIPTION.setSection(None)
assignment_SAMPLE_MICROSCOPY_SAMPLE_TYPE_MICROSCOPY_SAMPLE_DESCRIPTION.setPositionInForms(2)
assignment_SAMPLE_MICROSCOPY_SAMPLE_TYPE_MICROSCOPY_SAMPLE_DESCRIPTION.setShownEdit(True)

assignment_SAMPLE_MICROSCOPY_SAMPLE_TYPE_MICROSCOPY_SAMPLE_SIZE_IN_BYTES = tr.assignPropertyType(samp_type_MICROSCOPY_SAMPLE_TYPE, prop_type_MICROSCOPY_SAMPLE_SIZE_IN_BYTES)
assignment_SAMPLE_MICROSCOPY_SAMPLE_TYPE_MICROSCOPY_SAMPLE_SIZE_IN_BYTES.setMandatory(False)
assignment_SAMPLE_MICROSCOPY_SAMPLE_TYPE_MICROSCOPY_SAMPLE_SIZE_IN_BYTES.setSection(None)
assignment_SAMPLE_MICROSCOPY_SAMPLE_TYPE_MICROSCOPY_SAMPLE_SIZE_IN_BYTES.setPositionInForms(3)
assignment_SAMPLE_MICROSCOPY_SAMPLE_TYPE_MICROSCOPY_SAMPLE_SIZE_IN_BYTES.setShownEdit(False)

assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_VERSION = tr.assignPropertyType(exp_type_MICROSCOPY_EXPERIMENT, prop_type_MICROSCOPY_EXPERIMENT_VERSION)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_VERSION.setMandatory(False)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_VERSION.setSection(None)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_VERSION.setPositionInForms(4)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_VERSION.setShownEdit(False)

print ("Import of Microscopy Core Technology Master Data finished.")
