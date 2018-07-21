from __future__ import absolute_import
from qgis.PyQt.QtCore import *
from builtins import str
from qgis.PyQt.QtGui import QColor
from qgis.core import Qgis, QgsGeometry, QgsWkbTypes
from qgis.gui import QgsRubberBand
import psycopg2
from .. import pgRoutingLayer_utils as Utils
from .FunctionBase import FunctionBase

class Function(FunctionBase):
    
    @classmethod
    def getName(self):
        return 'trsp(via vertices)'
    
    @classmethod
    def getControlNames(self, version):
        return self.commonControls + self.commonBoxes + [
            'labelIds', 'lineEditIds', 'buttonSelectIds',
            'labelTurnRestrictSql', 'plainTextEditTurnRestrictSql'
        ]
    

    def isSupportedVersion(self, version):
        return version >= 2.1 

    def prepare(self, canvasItemList):
        resultPathsRubberBands = canvasItemList['paths']
        for path in resultPathsRubberBands:
            path.reset(Utils.getRubberBandType(False))
        canvasItemList['paths'] = []
    
    def getQuery(self, args):
        args['where_clause'] = self.whereClause(args['edge_table'], args['geometry'], args['BBOX'])
        return """
            SELECT seq, id1 AS _path, id2 AS _node, id3 AS _edge, cost AS _cost FROM pgr_trspViaVertices('
              SELECT %(id)s::int4 AS id,
                %(source)s::int4 AS source, %(target)s::int4 AS target,
                %(cost)s::float8 AS cost%(reverse_cost)s
              FROM %(edge_table)s
              %(where_clause)s',
              ARRAY[%(ids)s]::integer[],
              %(directed)s, %(has_reverse_cost)s,
              %(turn_restrict_sql)s)
            """ % args
    
    def getExportQuery(self, args):
        args['result_query'] = self.getQuery(args)

        query = """
            WITH
            result AS ( %(result_query)s )
            SELECT 
              CASE
                WHEN result._node = %(edge_table)s.%(source)s
                  THEN %(edge_table)s.%(geometry)s
                ELSE ST_Reverse(%(edge_table)s.%(geometry)s)
              END AS path_geom,
              result.*, %(edge_table)s.*
            FROM %(edge_table)s JOIN result
              ON %(edge_table)s.%(id)s = result._edge ORDER BY result.seq
            """ % args
        return query



    def getExportMergeQuery(self, args):
        return self.getExportOneSourceOneTargetMergeQuery(args)


    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        resultPathsRubberBands = canvasItemList['paths']
        rubberBand = None
        cur_path_id = -1

        for row in rows:
            cur2 = con.cursor()
            args['result_path_id'] = row[1]
            args['result_node_id'] = row[2]
            args['result_edge_id'] = row[3]
            args['result_cost'] = row[4]
            if args['result_path_id'] != cur_path_id:
                cur_path_id = args['result_path_id']
                if rubberBand:
                    resultPathsRubberBands.append(rubberBand)
                    rubberBand = None

                rubberBand = QgsRubberBand(mapCanvas, Utils.getRubberBandType(False))
                rubberBand.setColor(QColor(255, 0, 0, 128))
                rubberBand.setWidth(4)

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
                if geom.wkbType() == QgsWkbTypes.MultiLineString:
                    for line in geom.asMultiPolyline():
                        for pt in line:
                            rubberBand.addPoint(pt)
                elif geom.wkbType() == QgsWkbTypes.LineString:
                    for pt in geom.asPolyline():
                        rubberBand.addPoint(pt)

        if rubberBand:
            resultPathsRubberBands.append(rubberBand)
            rubberBand = None

    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
