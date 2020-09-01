from ch.systemsx.cisd.openbis.dss.etl.dto.api.impl import MaximumIntensityProjectionGenerationAlgorithm


class CustomExperimentMaximumIntensityProjectionGenerationAlgorithm(MaximumIntensityProjectionGenerationAlgorithm):
    """
    Custom MaximumIntensityProjectionGenerationAlgorithm that makes sure that the first
    timepoint in a series is registered for creation of the representative thumbnail.
    """

    def __init__(self, datasetTypeCode, width, height, filename):
        """
        Constructor
        """

        # Call the parent base constructor
        MaximumIntensityProjectionGenerationAlgorithm.__init__(self,
            datasetTypeCode, width, height, filename)

    def findMinTimepoint(self, information):
        mintimepoint = None
        for image in information.getImageDataSetStructure().getImages():
            timepoint = image.tryGetTimepoint()
            if timepoint is not None:
                if mintimepoint is None:
                    mintimepoint = timepoint
                else:
                    mintimepoint = min(mintimepoint, timepoint)
        return mintimepoint

    def generateImages(self, information, thumbnailDatasets, imageProvider):
        self.mintimepoint = self.findMinTimepoint(information)
        return super(CustomExperimentMaximumIntensityProjectionGenerationAlgorithm, self).generateImages(information, thumbnailDatasets, imageProvider)

    def imageToBeIgnored(self, image):
        """
        Overrides the parent imageToBeIgnored method. The selection of which
        series should be used to create the representative thumbnail is done
        elsewhere. Here we prevent the base
        MaximumIntensityProjectionGenerationAlgorithm.imageToBeIgnored() method
        to make a decision based on the timepoint (==0).
        """

        return image.tryGetTimepoint() != self.mintimepoint