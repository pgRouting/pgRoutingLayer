from __future__ import absolute_import
from builtins import str
from qgis.PyQt.QtCore import QPointF, QSizeF
from qgis.PyQt.QtGui import QTextDocument 
from qgis.core import QgsGeometry, Qgis, QgsTextAnnotation
from qgis.gui import *
import psycopg2
from .. import pgRoutingLayer_utils as Utils
from .FunctionBase import FunctionBase

class Function(FunctionBase):
    
    @classmethod
    def getName(self):
        return 'tsp(euclid)'
    
    @classmethod
    def getControlNames(self, version):
        return [
            'labelId', 'lineEditId',
            'labelSource', 'lineEditSource',
            'labelTarget', 'lineEditTarget',
            'labelIds', 'lineEditIds', 'buttonSelectIds',
            'labelSourceId', 'lineEditSourceId', 'buttonSelectSourceId',
            'labelTargetId', 'lineEditTargetId', 'buttonSelectTargetId'
        ]
    
    @classmethod
    def canExport(self):
        return False

    @classmethod
    def canExportMerged(self):
        return False

    def isSupportedVersion(self, version):
        return version >= 2.0 and version < 3.0

    def prepare(self, canvasItemList):
        resultNodesTextAnnotations = canvasItemList['annotations']
        for anno in resultNodesTextAnnotations:
            anno.setVisible(False)
        canvasItemList['annotations'] = []
    
    def getQuery(self, args):
        return """
            SELECT seq, id1 AS internal, id2 AS node, cost FROM pgr_tsp('
                SELECT id::int4,
                    ST_X(the_geom) AS x,
                    ST_Y(the_geom) AS y,
                    the_geom
                FROM  %(edge_table)s_vertices_pgr WHERE id IN (%(ids)s)',
            %(source_id)s::int4, %(target_id)s::int4)
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

    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        resultPathsRubberBands = canvasItemList['path']
        i = 0
        for row in rows:
            if i == 0:
                prevrow = row
                firstrow = row
                i += 1  
            cur2 = con.cursor()
            args['result_seq'] = row[0]
            args['result_source_id'] = prevrow[2]
            args['result_target_id'] = row[2]
            args['result_cost'] = row[3]
            query2 = """
                    SELECT ST_AsText( ST_MakeLine( 
                        (SELECT the_geom FROM  %(edge_table)s_vertices_pgr WHERE id = %(result_source_id)d),
                        (SELECT the_geom FROM  %(edge_table)s_vertices_pgr WHERE id = %(result_target_id)d)
                        ))
                """ % args
            ##Utils.logMessage(query2)
            cur2.execute(query2)
            row2 = cur2.fetchone()
            ##Utils.logMessage(str(row2[0]))
            assert row2, "Invalid result geometry. (path_id:%(result_path_id)d, saource_id:%(result_source_id)d, target_id:%(result_target_id)d)" % args

            geom = QgsGeometry().fromWkt(str(row2[0]))
            if geom.wkbType() == Qgis.WKBMultiLineString:
                for line in geom.asMultiPolyline():
                    for pt in line:
                        resultPathsRubberBands.addPoint(pt)
            elif geom.wkbType() == Qgis.WKBLineString:
                for pt in geom.asPolyline():
                    resultPathsRubberBands.addPoint(pt)
            prevrow = row
            lastrow = row
        
        args['result_source_id'] = lastrow[2]
        args['result_target_id'] = firstrow[2]
        args['result_cost'] = row[3]
        query2 = """
                SELECT ST_AsText( ST_MakeLine( 
                    (SELECT the_geom FROM  %(edge_table)s_vertices_pgr WHERE id = %(result_source_id)d),
                    (SELECT the_geom FROM  %(edge_table)s_vertices_pgr WHERE id = %(result_target_id)d)
                    ))
            """ % args
        ##Utils.logMessage(query2)
        cur2.execute(query2)
        row2 = cur2.fetchone()
        ##Utils.logMessage(str(row2[0]))
        assert row2, "Invalid result geometry. (path_id:%(result_path_id)d, saource_id:%(result_source_id)d, target_id:%(result_target_id)d)" % args

        geom = QgsGeometry().fromWkt(str(row2[0]))
        if geom.wkbType() == Qgis.WKBMultiLineString:
            for line in geom.asMultiPolyline():
                for pt in line:
                    resultPathsRubberBands.addPoint(pt)
        elif geom.wkbType() == Qgis.WKBLineString:
            for pt in geom.asPolyline():
                resultPathsRubberBands.addPoint(pt)





        ############ ANOTATIONS
        resultNodesTextAnnotations = canvasItemList['annotations']
        Utils.setStartPoint(geomType, args)
        Utils.setEndPoint(geomType, args)
        # return columns are 'seq', 'id1(internal index)', 'id2(node id)', 'cost'
        for row in rows:
            cur2 = con.cursor()
            args['result_seq'] = row[0]
            args['result_internal_id'] = row[1]
            args['result_node_id'] = row[2]
            args['result_cost'] = row[3]
            query2 = """
                SELECT ST_AsText(%(transform_s)s%(startpoint)s%(transform_e)s) FROM %(edge_table)s
                    WHERE %(source)s = %(result_node_id)d
                UNION
                SELECT ST_AsText(%(transform_s)s%(endpoint)s%(transform_e)s) FROM %(edge_table)s
                    WHERE %(target)s = %(result_node_id)d
            """ % args
            cur2.execute(query2)
            row2 = cur2.fetchone()
            assert row2, "Invalid result geometry. (node_id:%(result_node_id)d)" % args
            
            geom = QgsGeometry().fromWkt(str(row2[0]))
            pt = geom.asPoint()
            textDocument = QTextDocument("%(result_seq)d:%(result_node_id)d" % args)
            textAnnotation = QgsTextAnnotation(mapCanvas)
            textAnnotation.setMapPosition(geom.asPoint())
            textAnnotation.setFrameSize(QSizeF(textDocument.idealWidth(), 20))
            textAnnotation.setOffsetFromReferencePoint(QPointF(20, -40))
            textAnnotation.setDocument(textDocument)
            textAnnotation.update()
            resultNodesTextAnnotations.append(textAnnotation)
    
    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
