from __future__ import absolute_import
from .CostBase import CostBase

class Function(CostBase):

    minPGRversion = 2.2

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'pgr_dijkstraCost'

    def __init__(self, ui):
        CostBase.__init__(self, ui)
