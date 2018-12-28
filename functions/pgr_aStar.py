from __future__ import absolute_import
from .AstarBase import AstarBase

class Function(AstarBase):

    minPGRversion = 2.4

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'pgr_aStar'

    def __init__(self, ui):
        AstarBase.__init__(self, ui)
