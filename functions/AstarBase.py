from __future__ import absolute_import
from .DijkstraBase import DijkstraBase

class AstarBase(DijkstraBase):

    @classmethod
    def getControlNames(self, version):
        return self.commonControls + self.commonBoxes + self.astarControls + [
                'labelSourceIds', 'lineEditSourceIds', 'buttonSelectSourceIds',
                'labelTargetIds', 'lineEditTargetIds', 'buttonSelectTargetIds',
                ]

    def __init__(self, ui):
        DijkstraBase.__init__(self, ui)
