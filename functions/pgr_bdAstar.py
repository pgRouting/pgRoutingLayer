from __future__ import absolute_import
from .AstarBase import AstarBase

class Function(AstarBase):

    minPGRversion = 2.5

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'pgr_bdAstar'


    def __init__(self, ui):
        AstarBase.__init__(self, ui)
