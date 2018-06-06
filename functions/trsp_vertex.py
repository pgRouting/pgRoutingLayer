from __future__ import absolute_import
#from PyQt4.QtCore import *
#from PyQt4.QtGui import *
from builtins import str
from qgis.core import QGis, QgsGeometry
from qgis.gui import QgsRubberBand
import psycopg2
from .. import pgRoutingLayer_utils as Utils
from .FunctionBase import FunctionBase

class Function(FunctionBase):
    
    @classmethod
    def getName(self):
        return 'trsp(vertex)'
    
    @classmethod
    def getControlNames(self, version):
        return self.commonControls + self.commonBoxes + [
                'labelSourceId', 'lineEditSourceId', 'buttonSelectSourceId', 
                'labelTargetId', 'lineEditTargetId', 'buttonSelectTargetId',
                'labelTurnRestrictSql', 'plainTextEditTurnRestrictSql'
                ]                       

        return [
        ]
    
    def isSupportedVersion(self, version):
        return version >= 2.0 and version < 3.0

    def prepare(self, canvasItemList):
        resultPathRubberBand = canvasItemList['path']
        resultPathRubberBand.reset(Utils.getRubberBandType(False))
    
    def getQuery(self, args):
        args['where_clause'] = self.whereClause(args['edge_table'], args['geometry'], args['BBOX'])
        return """
            SELECT seq, id1 AS _node, id2 AS _edge, cost AS _cost FROM pgr_trsp('
              SELECT %(id)s::int4 AS id,
                %(source)s::int4 AS source,
                %(target)s::int4 AS target,
                %(cost)s::float8 AS cost%(reverse_cost)s
              FROM %(edge_table)s
              %(where_clause)s',
              %(source_id)s, %(target_id)s,
              %(directed)s, %(has_reverse_cost)s,
              %(turn_restrict_sql)s)
            """ % args

    def getExportQuery(self, args):
        return self.getJoinResultWithEdgeTable(args)

    def getExportMergeQuery(self, args):
        return self.getExportOneSourceOneTargetMergeQuery(args)


    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        resultPathRubberBand = canvasItemList['path']
        for row in rows:
            cur2 = con.cursor()
            args['result_node_id'] = row[1]
            args['result_edge_id'] = row[2]
            args['result_cost'] = row[3]
            if args['result_edge_id'] != -1:
                query2 = """
                    SELECT ST_AsText(%(transform_s)s%(geometry)s%(transform_e)s) FROM %(edge_table)s
                        WHERE %(source)s = %(result_node_id)d AND %(id)s = %(result_edge_id)d
                    UNION
                    SELECT ST_AsText(%(transform_s)sST_Reverse(%(geometry)s)%(transform_e)s) FROM %(edge_table)s
                        WHERE %(target)s = %(result_node_id)d AND %(id)s = %(result_edge_id)d;
                """ % args
                ##Utils.logMessage(query2)
                cur2.execute(query2)
                row2 = cur2.fetchone()
                ##Utils.logMessage(str(row2[0]))
                assert row2, "Invalid result geometry. (node_id:%(result_node_id)d, edge_id:%(result_edge_id)d)" % args
                
                geom = QgsGeometry().fromWkt(str(row2[0]))
                if geom.wkbType() == QGis.WKBMultiLineString:
                    for line in geom.asMultiPolyline():
                        for pt in line:
                            resultPathRubberBand.addPoint(pt)
                elif geom.wkbType() == QGis.WKBLineString:
                    for pt in geom.asPolyline():
                        resultPathRubberBand.addPoint(pt)
    
    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
