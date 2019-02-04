from __future__ import absolute_import
from .CostBase import CostBase


class Function(CostBase):

    minPGRversion = 2.5

    def __init__(self, ui):
        CostBase.__init__(self, ui)

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'pgr_bdDijkstraCost'
