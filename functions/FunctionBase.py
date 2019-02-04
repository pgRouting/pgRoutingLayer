from qgis.PyQt.QtCore import QSizeF, QPointF
from qgis.core import (QgsGeometry, QgsWkbTypes, QgsTextAnnotation)
from qgis.PyQt.QtGui import QColor, QTextDocument
from qgis.gui import QgsRubberBand, QgsMapCanvasAnnotationItem
from psycopg2 import sql

from pgRoutingLayer import pgRoutingLayer_utils as Utils


class FunctionBase(object):

    minPGRversion = 2.1

    # the mayority of the functions have this values
    exportButton = True
    exportMergeButton = True
    exportEdgeBase = False
    commonControls = [
        'labelId', 'lineEditId',
        'labelSource', 'lineEditSource',
        'labelTarget', 'lineEditTarget',
        'labelCost', 'lineEditCost',
        'labelReverseCost', 'lineEditReverseCost']
    commonBoxes = [
        'checkBoxUseBBOX',
        'checkBoxDirected',
        'checkBoxHasReverseCost']
    astarControls = [
        'labelX1', 'lineEditX1',
        'labelY1', 'lineEditY1',
        'labelX2', 'lineEditX2',
        'labelY2', 'lineEditY2',
        'labelAstarHeuristic', 'selectAstarHeuristic',
        'labelAstarFactor', 'selectAstarFactor',
        'labelAstarEpsilon', 'selectAstarEpsilon', 'showAstarEpsilon']

    def __init__(self, ui):
        self.ui = ui
        self.minVersion = 3.0
        self.maxVersion = 3.0

    @classmethod
    def getName(self):
        return ''

    @classmethod
    def getControlNames(self, version):
        return self.commonControls + self.commonBoxes + [
            'labelSourceIds', 'lineEditSourceIds', 'buttonSelectSourceIds',
            'labelTargetIds', 'lineEditTargetIds', 'buttonSelectTargetIds',
        ]

    @classmethod
    def isEdgeBase(self):
        ''' checks if EdgeBase is set. '''
        return self.exportEdgeBase

    @classmethod
    def canExport(self):
        ''' checks if exportButton is set '''
        return self.exportButton

    @classmethod
    def canExportMerged(self):
        ''' checks if exportMergeButton is set. '''
        return self.exportMergeButton

    @classmethod
    def isSupportedVersion(self, version):
        ''' returns true if version is greater than minPGRversio '''
        return version >= self.minPGRversion

    @classmethod
    def whereClause(self, table, geometry, bbox):
        ''' returns where clause for sql parameterising '''
        if bbox == ' ':
            return sql.SQL(' WHERE true ')
        else:
            return sql.SQL(' WHERE {0}.{1} {2}').format(table, geometry, bbox)

    def prepare(self, canvasItemList):
        pass

    @classmethod
    def getQuery(self, args):
        pass

    @classmethod
    def getExportQuery(self, args):
        pass

    @classmethod
    def getExportMergeQuery(self, args):
        pass

    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        pass

    def getJoinResultWithEdgeTable(self, args):
        '''returns a query which joins edge_table with result based on edge.id'''
        args['result_query'] = self.getQuery(args)

        query = sql.SQL("""
            WITH
            result AS ( {result_query} )
            SELECT
              CASE
                WHEN result._node = {edge_table}.{source}
                  THEN {edge_table}.{geometry}
                ELSE ST_Reverse({edge_table}.{geometry})
              END AS path_geom,
              result.*, {edge_table}.*
            FROM {edge_schema}.{edge_table} JOIN result
              ON {edge_table}.{id} = result._edge ORDER BY result.seq
            """).format(**args)
        return query

    def getExportManySourceManyTargetMergeQuery(self, args):
        ''' returns merge query for many source and many target '''
        queries = {}
        queries['result_query'] = self.getQuery(args)

        queries['geom_query'] = sql.SQL("""
            SELECT
              seq, result.path_name,
              CASE
                WHEN result._node = {edge_table}.{source}
                  THEN {edge_table}.{geometry}
                ELSE ST_Reverse({edge_table}.{geometry})
              END AS path_geom
            FROM {edge_schema}.{edge_table} JOIN result
              ON {edge_table}.{id} = result._edge
            """).format(**args)

        query = sql.SQL("""WITH
            result AS ( {result_query} ),
            with_geom AS ( {geom_query} ),
            one_geom AS (
                SELECT path_name, ST_LineMerge(ST_Union(path_geom)) AS path_geom
                FROM with_geom
                GROUP BY path_name
                ORDER BY path_name
            ),
            aggregates AS (
                SELECT
                    path_name, _start_vid, _end_vid,
                    SUM(_cost) AS agg_cost,
                    array_agg(_node ORDER BY _path_seq) AS _nodes,
                    array_agg(_edge ORDER BY _path_seq) AS _edges
                FROM result
                GROUP BY path_name, _start_vid, _end_vid
                ORDER BY _start_vid, _end_vid
            )
            SELECT row_number() over() as seq,
                path_name, _start_vid, _end_vid, agg_cost, _nodes, _edges,
                path_geom AS path_geom FROM aggregates JOIN one_geom
                USING (path_name)
            """).format(**queries)
        return query

    @classmethod
    def drawManyPaths(self, rows, columns, con, args, geomType, canvasItemList, mapCanvas):
        '''
            draws multi line string on the mapCanvas.
        '''
        resultPathsRubberBands = canvasItemList['paths']
        rubberBand = None
        cur_path_id = None
        for row in rows:
            cur2 = con.cursor()
            result_path_id = str(row[columns[0]])
            args['result_node_id'] = sql.Literal(row[columns[1]])
            args['result_edge_id'] = sql.Literal(row[columns[2]])

            if result_path_id != cur_path_id:
                cur_path_id = result_path_id
                if rubberBand:
                    resultPathsRubberBands.append(rubberBand)
                    rubberBand = None

                rubberBand = QgsRubberBand(mapCanvas, Utils.getRubberBandType(False))
                rubberBand.setColor(QColor(255, 0, 0, 128))
                rubberBand.setWidth(4)

            if row[columns[2]] != -1:
                query2 = sql.SQL("""
                    SELECT ST_AsText({transform_s}{geometry}{transform_e})
                    FROM {edge_schema}.{edge_table}
                    WHERE {source} = {result_node_id} AND {id} = {result_edge_id}

                    UNION

                    SELECT ST_AsText({transform_s}ST_Reverse({geometry}){transform_e})
                    FROM {edge_schema}.{edge_table}
                    WHERE {target} = {result_node_id} AND {id} = {result_edge_id}
                    """).format(**args).as_string(con)

                cur2.execute(query2)
                row2 = cur2.fetchone()

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

    @classmethod
    def drawOnePath(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        ''' draws  line string on the mapCanvas. '''
        resultPathRubberBand = canvasItemList['path']
        for row in rows:
                cur2 = con.cursor()
                args['result_node_id'] = sql.Literal(row[1])
                args['result_edge_id'] = sql.Literal(row[2])
                args['result_cost'] = row[3]
                if row[2] != -1:
                    query2 = sql.SQL("""
                        SELECT ST_AsText({geom_t} FROM {edge_schema}.{edge_table}
                            WHERE {source} = {result_node_id} AND {id} = {result_edge_id}
                        UNION
                        SELECT ST_AsText(ST_Reverse({geom_t}) FROM {edge_schema}.{edge_table}
                            WHERE {target} = {result_node_id} AND {id} = {result_edge_id};
                    """).format(**args)

                    cur2.execute(query2)
                    row2 = cur2.fetchone()

                    geom = QgsGeometry().fromWkt(str(row2[0]))
                    if geom.wkbType() == QgsWkbTypes.MultiLineString:
                        for line in geom.asMultiPolyline():
                            for pt in line:
                                resultPathRubberBand.addPoint(pt)
                    elif geom.wkbType() == QgsWkbTypes.LineString:
                        for pt in geom.asPolyline():
                            resultPathRubberBand.addPoint(pt)

    @classmethod
    def drawCostPaths(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        resultPathsRubberBands = canvasItemList['paths']
        rubberBand = None
        cur_path_id = -1
        for row in rows:
            cur2 = con.cursor()
            args['result_path_id'] = row[0]
            args['result_source_id'] = sql.Literal(row[1])
            args['result_target_id'] = sql.Literal(row[2])
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
                query2 = sql.SQL("""
                    SELECT ST_AsText( ST_MakeLine(
                        (SELECT {geometry_vt} FROM  {vertex_schema}.{vertex_table} WHERE id = {result_source_id}),
                        (SELECT {geometry_vt} FROM  {vertex_schema}.{vertex_table} WHERE id = {result_target_id})
                        ))
                    """).format(**args)
                # Utils.logMessage(query2)
                cur2.execute(query2)
                row2 = cur2.fetchone()
                # Utils.logMessage(str(row2[0]))

                geom = QgsGeometry().fromWkt(str(row2[0]))
                if geom.wkbType() == QgsWkbTypes.MultiLineString:
                    for line in geom.asMultiPolyline():
                        for pt in line:
                            rubberBand.addPoint(pt)
                elif geom.wkbType() == QgsWkbTypes.LineString:
                    for pt in geom.asPolyline():
                        rubberBand.addPoint(pt)

        # TODO label the edge instead of labeling the target points
        if rubberBand:
            resultPathsRubberBands.append(rubberBand)
            rubberBand = None
        resultNodesTextAnnotations = canvasItemList['annotations']
        for row in rows:
            cur2 = con.cursor()
            args['result_seq'] = row[0]
            args['result_source_id'] = sql.Literal(row[1])
            result_target_id = row[2]
            args['result_target_id'] = sql.Literal(result_target_id)
            result_cost = row[3]
            query2 = sql.SQL("""
                SELECT ST_AsText( ST_startPoint({geometry}) ) FROM {edge_schema}.{edge_table}
                    WHERE {source} = {result_target_id}
                UNION
                SELECT ST_AsText( ST_endPoint( {geometry} ) ) FROM {edge_schema}.{edge_table}
                    WHERE {target} = {result_target_id}
                """).format(**args)
            cur2.execute(query2)
            row2 = cur2.fetchone()

            geom = QgsGeometry().fromWkt(str(row2[0]))
            pt = geom.asPoint()
            textDocument = QTextDocument("{0!s}:{1}".format(result_target_id, result_cost))
            textAnnotation = QgsTextAnnotation()
            textAnnotation.setMapPosition(geom.asPoint())
            textAnnotation.setFrameSize(QSizeF(textDocument.idealWidth(), 20))
            textAnnotation.setFrameOffsetFromReferencePoint(QPointF(20, -40))
            textAnnotation.setDocument(textDocument)

            QgsMapCanvasAnnotationItem(textAnnotation, mapCanvas)
            resultNodesTextAnnotations.append(textAnnotation)
