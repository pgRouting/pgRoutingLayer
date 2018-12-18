from __future__ import absolute_import
from builtins import str
from qgis.PyQt.QtCore import QSizeF, QPointF
from qgis.PyQt.QtGui import QColor, QTextDocument
from qgis.core import QgsGeometry, Qgis, QgsTextAnnotation, QgsWkbTypes, QgsAnnotation
from qgis.gui import QgsRubberBand, QgsMapCanvasAnnotationItem
from psycopg2 import sql
from pgRoutingLayer import pgRoutingLayer_utils as Utils
from .CostBase import CostBase

class Function(CostBase):

    minPGRversion = 2.4

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'pgr_aStarCost'

    @classmethod
    def getControlNames(self, version):
        ''' returns control names for this function. '''
        return self.commonControls + self.commonBoxes + self.astarControls + [
                'labelSourceIds', 'lineEditSourceIds', 'buttonSelectSourceIds',
                'labelTargetIds', 'lineEditTargetIds', 'buttonSelectTargetIds',
                ]

    def __init__(self, ui):
        CostBase.__init__(self, ui)
