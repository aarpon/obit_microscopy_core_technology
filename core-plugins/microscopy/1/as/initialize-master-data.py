# -*- coding: utf-8 -*-
import ch.systemsx.cisd.openbis.generic.server.jython.api.v1.DataType as DataType

print ("Importing Master Data...")

tr = service.transaction()

# ==============================================================================
#
# FILE FORMATS
#
# ==============================================================================

# FCS file format
file_type_FCS = tr.getOrCreateNewFileFormatType('FCS')
file_type_FCS.setDescription('Flow Cytometry Standard file.')

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
data_set_type_HCS_IMAGE_CONTAINER_RAW = tr.getOrCreateNewDataSetType('MICROSCOPY_IMG')
data_set_type_HCS_IMAGE_CONTAINER_RAW.setDescription('Generic Microscopy Image.')
data_set_type_HCS_IMAGE_CONTAINER_RAW.setDataSetKind('PHYSICAL')  # Is this correct?
data_set_type_HCS_IMAGE_CONTAINER_RAW.setMainDataSetPattern(None)
data_set_type_HCS_IMAGE_CONTAINER_RAW.setMainDataSetPath(None)
data_set_type_HCS_IMAGE_CONTAINER_RAW.setDeletionDisallowed(False)

# MICROSCOPY_IMG_CONTAINER
data_set_type_MICROSCOPY_IMG_OVERVIEW = tr.getOrCreateNewDataSetType('MICROSCOPY_IMG_CONTAINER')
data_set_type_MICROSCOPY_IMG_OVERVIEW.setDescription('Generic Microscopy Image Container.')
data_set_type_MICROSCOPY_IMG_OVERVIEW.setDataSetKind('CONTAINER')
data_set_type_MICROSCOPY_IMG_OVERVIEW.setMainDataSetPattern(None)
data_set_type_MICROSCOPY_IMG_OVERVIEW.setMainDataSetPath(None)
data_set_type_MICROSCOPY_IMG_OVERVIEW.setDeletionDisallowed(False)

# MICROSCOPY_IMG_OVERVIEW
data_set_type_MICROSCOPY_IMG_OVERVIEW = tr.getOrCreateNewDataSetType('MICROSCOPY_IMG_OVERVIEW')
data_set_type_MICROSCOPY_IMG_OVERVIEW.setDescription('Overview Microscopy Image. Generated from raw images.')
data_set_type_MICROSCOPY_IMG_OVERVIEW.setDataSetKind('PHYSICAL')
data_set_type_MICROSCOPY_IMG_OVERVIEW.setMainDataSetPattern(None)
data_set_type_MICROSCOPY_IMG_OVERVIEW.setMainDataSetPath(None)
data_set_type_MICROSCOPY_IMG_OVERVIEW.setDeletionDisallowed(False)

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

# Assignments

assignment_DATA_SET_MICROSCOPY_IMG_OVERVIEW_RESOLUTION = tr.assignPropertyType(data_set_type_MICROSCOPY_IMG_OVERVIEW, prop_type_RESOLUTION)
assignment_DATA_SET_MICROSCOPY_IMG_OVERVIEW_RESOLUTION.setMandatory(False)
assignment_DATA_SET_MICROSCOPY_IMG_OVERVIEW_RESOLUTION.setSection(None)
assignment_DATA_SET_MICROSCOPY_IMG_OVERVIEW_RESOLUTION.setPositionInForms(2)

assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_NAME = tr.assignPropertyType(exp_type_MICROSCOPY_EXPERIMENT, prop_type_MICROSCOPY_EXPERIMENT_NAME)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_NAME.setMandatory(False)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_NAME.setSection(None)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_NAME.setPositionInForms(1)

assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_DESCRIPTION = tr.assignPropertyType(exp_type_MICROSCOPY_EXPERIMENT, prop_type_MICROSCOPY_EXPERIMENT_DESCRIPTION)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_DESCRIPTION.setMandatory(False)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_DESCRIPTION.setSection(None)
assignment_EXPERIMENT_MICROSCOPY_EXPERIMENT_MICROSCOPY_EXPERIMENT_DESCRIPTION.setPositionInForms(2)

print ("Import of Master Data finished.")
