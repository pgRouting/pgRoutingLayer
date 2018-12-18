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

    minPGRversion = 2.1

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'pgr_dijkstraCost'

    def __init__(self, ui):
        CostBase.__init__(self, ui)
