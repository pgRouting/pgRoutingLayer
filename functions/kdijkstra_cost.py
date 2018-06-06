from __future__ import absolute_import
from builtins import str
from qgis.PyQt.QtCore import QSizeF, QPointF
from qgis.PyQt.QtGui import QColor
from qgis.core import QGis, QgsGeometry
from qgis.gui import QgsRubberBand, QgsTextAnnotationItem
import psycopg2
from .. import pgRoutingLayer_utils as Utils
from .FunctionBase import FunctionBase

class Function(FunctionBase):
    
    @classmethod
    def getName(self):
        return 'kdijkstra(cost)'
    
    @classmethod
    def isSupportedVersion(self, version):
        # Deprecated on version 2.2
        return version >= 2.0 and version < 2.2

    @classmethod
    def getControlNames(self, version):
        # version 2.0 has only one to many
        return self.commonControls + self.commonBoxes + [
                'labelSourceId', 'lineEditSourceId', 'buttonSelectSourceId',
                'labelTargetIds', 'lineEditTargetIds', 'buttonSelectTargetIds',
                ]

    
    @classmethod
    def canExport(self):
        return True
    
    @classmethod
    def canExportMerged(self):
        return False
    
    def prepare(self, canvasItemList):
        resultNodesTextAnnotations = canvasItemList['annotations']
        for anno in resultNodesTextAnnotations:
            anno.setVisible(False)
            self.iface.mapCanvas().scene().removeItem(anno)
        canvasItemList['annotations'] = []
    
    def getQuery(self, args):
        args['where_clause'] = self.whereClause(args['edge_table'], args['geometry'], args['BBOX'])
        return """
            SELECT seq, id1 AS source, id2 AS target, cost FROM pgr_kdijkstraCost('
                SELECT %(id)s::int4 AS id,
                    %(source)s::int4 AS source,
                    %(target)s::int4 AS target,
                    %(cost)s::float8 AS cost%(reverse_cost)s
                    FROM %(edge_table)s
                    %(where_clause)s',
                %(source_id)s, array[%(target_ids)s], %(directed)s, %(has_reverse_cost)s)""" % args
    
    def getExportQuery(self, args):
        args['result_query'] = self.getQuery(args)
        args['vertex_table'] = """ 
            %(edge_table)s_vertices_pgr
            """ % args

        return """
            WITH
            result AS ( %(result_query)s )
            SELECT result.*, ST_MakeLine(a.the_geom, b.the_geom) AS path_geom

            FROM result
            JOIN  %(vertex_table)s AS a ON (source = a.id)
            JOIN  %(vertex_table)s AS b ON (target = b.id)
            """ % args


    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        resultPathsRubberBands = canvasItemList['paths']
        rubberBand = None
        cur_path_id = -1
        for row in rows:
            cur2 = con.cursor()
            args['result_path_id'] = row[0]
            args['result_source_id'] = row[1]
            args['result_target_id'] = row[2]
            args['result_cost'] = row[3]
            if args['result_path_id'] != cur_path_id:
                cur_path_id = args['result_path_id']
                if rubberBand:
                    resultPathsRubberBands.append(rubberBand)
                    rubberBand = None

                rubberBand = QgsRubberBand(mapCanvas, Utils.getRubberBandType(False))
                rubberBand.setColor(QColor(255, 0, 0, 128))
                rubberBand.setWidth(4)
            if args['result_cost'] != -1:
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
                if geom.wkbType() == QGis.WKBMultiLineString:
                    for line in geom.asMultiPolyline():
                        for pt in line:
                            rubberBand.addPoint(pt)
                elif geom.wkbType() == QGis.WKBLineString:
                    for pt in geom.asPolyline():
                        rubberBand.addPoint(pt)

        if rubberBand:
            resultPathsRubberBands.append(rubberBand)
            rubberBand = None


        resultNodesTextAnnotations = canvasItemList['annotations']
        Utils.setStartPoint(geomType, args)
        Utils.setEndPoint(geomType, args)
        for row in rows:
            cur2 = con.cursor()
            args['result_seq'] = row[0]
            args['result_source_id'] = row[1]
            args['result_target_id'] = row[2]
            args['result_cost'] = row[3]
            query2 = """
                SELECT ST_AsText(%(transform_s)s%(startpoint)s%(transform_e)s) FROM %(edge_table)s
                    WHERE %(source)s = %(result_target_id)d
                UNION
                SELECT ST_AsText(%(transform_s)s%(endpoint)s%(transform_e)s) FROM %(edge_table)s
                    WHERE %(target)s = %(result_target_id)d
            """ % args
            cur2.execute(query2)
            row2 = cur2.fetchone()
            assert row2, "Invalid result geometry. (target_id:%(result_target_id)d)" % args
            
            geom = QgsGeometry().fromWkt(str(row2[0]))
            pt = geom.asPoint()
            textDocument = QTextDocument("%(result_target_id)d:%(result_cost)f" % args)
            textAnnotation = QgsTextAnnotationItem(mapCanvas)
            textAnnotation.setMapPosition(geom.asPoint())
            textAnnotation.setFrameSize(QSizeF(textDocument.idealWidth(), 20))
            textAnnotation.setOffsetFromReferencePoint(QPointF(20, -40))
            textAnnotation.setDocument(textDocument)
            
            textAnnotation.update()
            resultNodesTextAnnotations.append(textAnnotation)
            canvasItemList['annotations'] = resultNodesTextAnnotations

    
    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
