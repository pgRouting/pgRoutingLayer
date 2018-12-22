from __future__ import absolute_import
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsGeometry, QgsWkbTypes
from qgis.gui import QgsRubberBand
from psycopg2 import sql
from pgRoutingLayer import pgRoutingLayer_utils as Utils
from .FunctionBase import FunctionBase

class Function(FunctionBase):

    minPGRversion = 2.1

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'pgr_KSP'

    @classmethod
    def getControlNames(self, version):
        ''' returns control names. '''
        return self.commonControls + self.commonBoxes + [
            'labelSourceId', 'lineEditSourceId', 'buttonSelectSourceId',
            'labelTargetId', 'lineEditTargetId', 'buttonSelectTargetId',
            'labelPaths', 'lineEditPaths',
            'checkBoxHeapPaths'
            ]

    def prepare(self, canvasItemList):
        resultPathsRubberBands = canvasItemList['paths']
        for path in resultPathsRubberBands:
            path.reset(Utils.getRubberBandType(False))
        canvasItemList['paths'] = []

    def getQuery(self, args):
        ''' returns the sql query in required signature format of pgr_KSP '''
        return sql.SQL("""
            SELECT seq,
              '(' || {source_id} || ', ' ||  {target_id} || ')-' || path_id AS path_name,
              path_id AS _path_id,
              path_seq AS _path_seq,
              node AS _node,
              edge AS _edge,
              cost AS _cost
            FROM pgr_KSP(' {innerQuery} ',
                {source_id}, {target_id}, {Kpaths}, {directed}, {heap_paths})
            """).format(**args)

    def getExportQuery(self, args):
        return self.getJoinResultWithEdgeTable(args)


    def getExportMergeQuery(self, args):
        args['result_query'] = self.getQuery(args)
        return sql.SQL("""WITH
            result AS ( {result_query} ),
            with_geom AS (
                SELECTseq, result.path_name,
                CASE
                    WHEN result._node = et.{source}
                      THEN et.{geometry}
                    ELSE ST_Reverse(et.{geometry})
                END AS path_geom
                FROM {edge_table} AS et JOIN result ON et.{id} = result._edge
            ),
            one_geom AS (
                SELECT path_name, ST_LineMerge(ST_Union(path_geom)) AS path_geom
                FROM with_geom GROUP BY path_name ORDER BY path_name
            ),
            aggregates AS (
                SELECT
                path_name, _path_id,
                SUM(_cost) AS agg_cost,
                array_agg(_node ORDER BY _path_seq) AS _nodes,
                array_agg(_edge ORDER BY _path_seq) AS _edges
                FROM result
                GROUP BY path_name, _path_id
            )
            SELECT row_number() over() as seq,
            _path_id, path_name, _nodes, _edges, agg_cost, path_geom
            FROM aggregates JOIN one_geom USING (path_name) ORDER BY _path_id
        """).format(**args)


    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        ''' draw the result '''
        resultPathsRubberBands = canvasItemList['paths']
        rubberBand = None
        cur_route_id = -1
        for row in rows:
            cur2 = con.cursor()

            args['result_route_id'] = row[2]
            args['result_node_id'] = sql.Literal(row[4])
            args['result_edge_id'] = sql.Literal(row[5])
            args['result_cost'] = row[6]

            if args['result_route_id'] != cur_route_id:
                cur_route_id = args['result_route_id']
                if rubberBand:
                    resultPathsRubberBands.append(rubberBand)
                    rubberBand = None

                rubberBand = QgsRubberBand(mapCanvas, Utils.getRubberBandType(False))
                rubberBand.setColor(QColor(255, 0, 0, 128))
                rubberBand.setWidth(4)

            if row[5] != -1:
                query2 = sql.SQL("""
                    SELECT ST_AsText({geometry}) FROM {edge_table}
                        WHERE {source} = {result_node_id} AND {id} = {result_edge_id}
                    UNION
                    SELECT ST_AsText({geometry}) FROM {edge_table}
                        WHERE {target} = {result_node_id} AND {id} = {result_edge_id}
                    """).format(**args)
                Utils.logMessage(query2.as_string(con))
                cur2.execute(query2)
                row2 = cur2.fetchone()
                ##Utils.logMessage(str(row2[0]))
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
