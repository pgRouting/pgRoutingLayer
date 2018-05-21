from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import psycopg2
from .. import pgRoutingLayer_utils as Utils
from FunctionBase import FunctionBase

class Function(FunctionBase):
    ''' returns function name '''
    @classmethod
    def getName(self):
        return 'pgr_dijkstraCost'

    @classmethod
    def isSupportedVersion(self, version):
        # valid starting pgr v2.1
        return version >= 2.1


    @classmethod
    def canExportQuery(self):
        return False

    @classmethod
    def canExportMerged(self):
        return False



    def prepare(self, canvasItemList):
        resultNodesTextAnnotations = canvasItemList['annotations']
        for anno in resultNodesTextAnnotations:
            anno.setVisible(False)
        canvasItemList['annotations'] = []


    """ pgr_dijkstraCost returns cost if there exists a path, below function gives unique row_number
    to each row having start vertex,end vertex,cost of shortest path between them,path name."""

    def getQuery(self, args):
        args['where_clause'] = self.whereClause(args['edge_table'], args['geometry'], args['BBOX'])
        return """
            SELECT row_number() over() AS seq,
                   start_vid , end_vid, agg_cost AS cost,
                    '(' || start_vid || ',' || end_vid || ')' AS path_name
            FROM pgr_dijkstraCost('
              SELECT %(id)s AS id,
                %(source)s AS source,
                %(target)s AS target,
                %(cost)s AS cost
                %(reverse_cost)s
                FROM %(edge_table)s
                %(where_clause)s
                ',
              array[%(source_ids)s]::BIGINT[], array[%(target_ids)s]::BIGINT[], %(directed)s)
            """ % args

''' makes line geometry for each pair of vertex from the result query. '''
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
            JOIN  %(vertex_table)s AS a ON (start_vid = a.id)
            JOIN  %(vertex_table)s AS b ON (end_vid = b.id)
            """ % args



''' draws the result on mapCanvas. '''
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



    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
