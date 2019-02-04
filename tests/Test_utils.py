import pgRoutingLayer_utils as utils
import unittest
import sys
from qgis.core import *
from qgis.gui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *



class TestUtils(unittest.TestCase):

    def test_setStartPoint_1(self):
        args = { 'geometry': 'test_geom','table' : 'test_table'}
        geomType = 'ST_LineString'
        utils.setStartPoint(geomType,args)
        self.assertEqual(args['startpoint'], 'ST_StartPoint(test_geom)')

    def test_setStartPoint_2(self):
        args = { 'geometry': 'test_geom','table' : 'test_table'}
        geomType = 'ST_MultiLineString'
        utils.setStartPoint(geomType,args)
        self.assertEqual(args['startpoint'], 'ST_StartPoint(ST_GeometryN(test_geom, 1))')

    def test_setEndPoint_1(self):
        args = { 'geometry': 'test_geom','table' : 'test_table'}
        geomType = 'ST_LineString'
        utils.setEndPoint(geomType,args)
        self.assertEqual(args['endpoint'], 'ST_EndPoint(test_geom)')

    def test_setEndPoint_2(self):
        args = { 'geometry': 'test_geom','table' : 'test_table'}
        geomType = 'ST_MultiLineString'
        utils.setEndPoint(geomType,args)
        self.assertEqual(args['endpoint'], 'ST_EndPoint(ST_GeometryN(test_geom, 1))')

    def test_isSIPv2(self):
        self.assertTrue(utils.isSIPv2())

    def test_getStringValue(self):
        setting = QSettings()
        setting.setValue('/pgRoutingLayer/Database', 99)
        self.assertEqual(utils.getStringValue(setting,'/pgRoutingLayer/Database', 99) ,'99')

    def test_getBoolValue(self):
        setting = QSettings()
        setting.setValue('/pgRoutingLayer/Database', 99)
        self.assertTrue(utils.getBoolValue(setting,'/pgRoutingLayer/Database', 99))


    def test_getDestinationCrs(self):
        QApplication(sys.argv)
        # create a map canvas widget
        canvas = QgsMapCanvas()
        canvas.setCanvasColor(QColor('white'))
        canvas.enableAntiAliasing(True)
        canvas.setMinimumSize(800, 600)
        # load a shapefile
        layer = QgsVectorLayer('test_data' ,'poly', 'ogr')
        # add the layer to the canvas and zoom to it
        QgsMapLayerRegistry.instance().addMapLayer(layer)
        canvas.setLayerSet([QgsMapCanvasLayer(layer)])
        canvas.setExtent(layer.extent())
        self.assertIsNotNone(utils.getDestinationCrs(canvas))

    def test_getCanvasSrid(self):
        crs = QgsCoordinateReferenceSystem()
        crs.createFromProj4("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
        self.assertEqual(utils.getCanvasSrid(crs) ,0)

    def test_getRubberBandType_1(self):
        isPolygon = True
        self.assertEqual(utils.getRubberBandType(isPolygon),2)

    def test_getRubberBandType_2(self):
        isPolygon = False
        self.assertEqual(utils.getRubberBandType(isPolygon),1)

    def test_getNodeQuery(self):
        args = {'geometry' : 'test_geom','source': 1,'startpoint' : 10,'edge_table':'test_Table','target':100,'endpoint':90}
        expected_sql=  """
        WITH node AS (
            SELECT id::int4,
                ST_X(test_geom) AS x,
                ST_Y(test_geom) AS y,
                test_geom
                FROM (
                    SELECT 1::int4 AS id,
                        ST_StartPoint(ST_GeometryN(test_geom, 1)) AS test_geom
                        FROM test_Table
                    UNION
                    SELECT 100::int4 AS id,
                        ST_EndPoint(ST_GeometryN(test_geom, 1)) AS test_geom
                        FROM test_Table
                ) AS node
        )"""
        self.maxDiff = None
        geomType = 'ST_MultiLineString'
        self.assertMultiLineEqual(utils.getNodeQuery(args,geomType),expected_sql)

if __name__ == '__main__':
    unittest.main()
