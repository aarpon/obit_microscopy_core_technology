# -*- coding: utf-8 -*-

"""
Created on Apr 27, 2016

@author: Aaron Ponti
"""


class GlobalSettings(object):
    '''
    Store global settings to be used in the dropbox.
    '''

    # Image resolutions to be used to generate the images ("thumbnails") that
    # are displayed in the image viewer. Examples:
    #
    # ["128x128"]
    # ["128x128", "256x256"] 
    # 
    # Set to [] to disable generation of the thumbnails. If ImageResolutions is
    # set to [], the image viewer will generate the views on the fly at the
    # full the resolution and at 1/4 of the full resolution (in X and Y). Please 
    # notice that a minimum resolution of 128x128 is enforced. 
    ImageResolutions =  []
