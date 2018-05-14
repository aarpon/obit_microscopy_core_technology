# -*- coding: utf-8 -*-

'''
Created on Apr 27, 2016

@author: Aaron Ponti
'''

from ch.systemsx.cisd.openbis.dss.etl.dto.api.impl import MaximumIntensityProjectionGenerationAlgorithm


class VisitronTIFFNDMaximumIntensityProjectionGenerationAlgorithm(MaximumIntensityProjectionGenerationAlgorithm):
    '''
    Custom MaximumIntensityProjectionGenerationAlgorithm for YouScope Experiment Series
    that makes sure that the first timepoint in a series is registered for
    creation of the representative thumbnail. 
    '''


    def __init__(self, datasetTypeCode, width, height, filename):
        """
        Constructor
        """

        # Call the parent base constructor
        MaximumIntensityProjectionGenerationAlgorithm.__init__(self,
            datasetTypeCode, width, height, filename)


    def imageToBeIgnored(self, image):
        """
        Overrides the parent imageToBeIgnored method. The selection of which
        series should be used to create the representative thumbnail is done
        in VisitronSTKNDCompositeDatasetConfig. Here we prevent the base 
        MaximumIntensityProjectionGenerationAlgorithm.imageToBeIgnored() method
        to make a decision based on the timepoint (== 0), since we cannot know
        which is the first time point in an exported Leica TIFF Series.
        """

        return False
