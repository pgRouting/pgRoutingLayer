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

    version = 2.0

    
    @classmethod
    def getName(self):
        return 'ksp'
    
    @classmethod
    def getControlNames(self, version):
        # function pgr_ksp(text,integer,integer,integer, boolean)
        # boolean is has_rcost
        # only works for directed graph
        self.version = version
        if (self.version < 2.1):
            return [
                'labelId', 'lineEditId',
                'labelSource', 'lineEditSource',
                'labelTarget', 'lineEditTarget',
                'labelCost', 'lineEditCost',
                'labelReverseCost', 'lineEditReverseCost',
                'labelSourceId', 'lineEditSourceId', 'buttonSelectSourceId',
                'labelTargetId', 'lineEditTargetId', 'buttonSelectTargetId',
                'labelPaths', 'lineEditPaths',
                'checkBoxHasReverseCost'
                ]
        else:
            # function pgr_ksp(text,bigint,bigint,integer,boolean,boolean)
            return [
                'labelId', 'lineEditId',
                'labelSource', 'lineEditSource',
                'labelTarget', 'lineEditTarget',
                'labelCost', 'lineEditCost',
                'labelReverseCost', 'lineEditReverseCost',
                'labelSourceId', 'lineEditSourceId', 'buttonSelectSourceId',
                'labelTargetId', 'lineEditTargetId', 'buttonSelectTargetId',
                'labelPaths', 'lineEditPaths',
                'checkBoxDirected',
                'checkBoxHasReverseCost',
                'checkBoxHeapPaths'
                ]

    def prepare(self, canvasItemList):
        resultPathsRubberBands = canvasItemList['paths']
        for path in resultPathsRubberBands:
            path.reset(Utils.getRubberBandType(False))
        canvasItemList['paths'] = []

    def getQuery(self, args):
        if (self.version < 2.1):
            return """
                SELECT
                  seq, id1 AS _route,
                  id2 AS _node, id3 AS _edge,
                  cost AS _cost
                FROM pgr_ksp('
                  SELECT %(id)s::int4 AS id,
                    %(source)s::int4 AS source,
                    %(target)s::int4 AS target,
                    %(cost)s::float8 AS cost
                    %(reverse_cost)s
                  FROM %(edge_table)s
                  WHERE %(edge_table)s.%(geometry)s && %(BBOX)s',
                %(source_id)s, %(target_id)s, %(paths)s, %(has_reverse_cost)s)""" % args
        else:
            return """
                SELECT seq,
                  '(' || %(source_id)s || ', ' ||  %(target_id)s || ')-' || path_id AS path_name,
                  path_id AS _path_id,
                  path_seq AS _path_seq,
                  node AS _node,
                  edge AS _edge,
                  cost AS _cost
                FROM pgr_ksp('
                  SELECT %(id)s AS id,
                    %(source)s AS source,
                    %(target)s AS target,
                    %(cost)s AS cost
                    %(reverse_cost)s
                  FROM %(edge_table)s
                  WHERE %(edge_table)s.%(geometry)s && %(BBOX)s',
                  %(source_id)s, %(target_id)s, %(paths)s,
                  %(directed)s, %(heap_paths)s)""" % args

    def getExportQuery(self, args):
        return self.getJoinResultWithEdgeTable(args)


    def getExportMergeQuery(self, args):
        if self.version < 2.1:

            args['result_query'] = self.getQuery(args)

            args['with_geom_query'] = """
                SELECT 
                  seq, _route,
                  CASE
                    WHEN result._node = %(edge_table)s.%(source)s
                      THEN %(edge_table)s.%(geometry)s
                    ELSE ST_Reverse(%(edge_table)s.%(geometry)s)
                  END AS path_geom
                FROM %(edge_table)s JOIN result
                  ON %(edge_table)s.%(id)s = result._edge 
                """ % args

            args['one_geom_query'] = """
                SELECT _route, ST_LineMerge(ST_Union(path_geom)) AS path_geom
                FROM with_geom
                GROUP BY _route
                ORDER BY _route
                """ % args

            args['aggregates_query'] = """SELECT
                _route,
                SUM(_cost) AS agg_cost,
                array_agg(_node ORDER BY seq) AS _nodes,
                array_agg(_edge ORDER BY seq) AS _edges
                FROM result
                GROUP BY _route
                """

            query = """WITH
                result AS ( %(result_query)s ),
                with_geom AS ( %(with_geom_query)s ),
                one_geom AS ( %(one_geom_query)s ),
                aggregates AS ( %(aggregates_query)s )
                SELECT row_number() over() as seq,
                _route, _nodes, _edges, agg_cost,
                path_geom FROM aggregates JOIN one_geom
                USING (_route)
                """ % args

        else:

            args['result_query'] = self.getQuery(args)

            args['with_geom_query'] = """
                SELECT 
                  seq, result.path_name,
                  CASE
                    WHEN result._node = %(edge_table)s.%(source)s
                      THEN %(edge_table)s.%(geometry)s
                    ELSE ST_Reverse(%(edge_table)s.%(geometry)s)
                  END AS path_geom
                FROM %(edge_table)s JOIN result
                  ON %(edge_table)s.%(id)s = result._edge 
                """ % args

            args['one_geom_query'] = """
                SELECT path_name, ST_LineMerge(ST_Union(path_geom)) AS path_geom
                FROM with_geom
                GROUP BY path_name
                ORDER BY path_name
                """ % args

            args['aggregates_query'] = """SELECT
                path_name, _path_id,
                SUM(_cost) AS agg_cost,
                array_agg(_node ORDER BY _path_seq) AS _nodes,
                array_agg(_edge ORDER BY _path_seq) AS _edges
                FROM result
                GROUP BY path_name, _path_id
                """

            query = """WITH
                result AS ( %(result_query)s ),
                with_geom AS ( %(with_geom_query)s ),
                one_geom AS ( %(one_geom_query)s ),
                aggregates AS ( %(aggregates_query)s )
                SELECT row_number() over() as seq,
                    _path_id, path_name, _nodes, _edges, agg_cost,
                    path_geom FROM aggregates JOIN one_geom 
                    USING (path_name)
                    ORDER BY _path_id
                """ % args

        return query


    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        resultPathsRubberBands = canvasItemList['paths']
        rubberBand = None
        cur_route_id = -1
        for row in rows:
            cur2 = con.cursor()

            if self.version < 2.1:
                args['result_route_id'] = row[1]
                args['result_node_id'] = row[2]
                args['result_edge_id'] = row[3]
                args['result_cost'] = row[4]
            else:
                args['result_route_id'] = row[2]
                args['result_node_id'] = row[4]
                args['result_edge_id'] = row[5]
                args['result_cost'] = row[6]

            if args['result_route_id'] != cur_route_id:
                cur_route_id = args['result_route_id']
                if rubberBand:
                    resultPathsRubberBands.append(rubberBand)
                    rubberBand = None

                rubberBand = QgsRubberBand(mapCanvas, Utils.getRubberBandType(False))
                rubberBand.setColor(QColor(255, 0, 0, 128))
                rubberBand.setWidth(4)

            if args['result_edge_id'] != -1:
                #if args['result_edge_id'] != 0: # pgRouting <= 2.0.0rc1
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
                assert row2, "Invalid result geometry. (route_id:%(result_route_id)d, node_id:%(result_node_id)d, edge_id:%(result_edge_id)d)" % args

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
