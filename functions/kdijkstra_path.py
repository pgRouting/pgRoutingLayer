from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import psycopg2
from .. import pgRoutingLayer_utils as Utils
from FunctionBase import FunctionBase

class Function(FunctionBase):

    @classmethod
    def getName(self):
        return 'kdijkstra(path)'

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


    def prepare(self, canvasItemList):
        resultPathsRubberBands = canvasItemList['paths']
        for path in resultPathsRubberBands:
            path.reset(Utils.getRubberBandType(False))
        canvasItemList['paths'] = []


    """ pgr_kdijkstraPath gives shortest path from one startpoint to many target points. Its signature is:
    pgr_kdijkstraPath(sql_query,startpoint,array[targets],directed,has_reverse_cost)"""

    # SELECT startpoint,targets,edges,cost from result of pgr_kdijkstraPath.
    def getQuery(self, args):
        args['where_clause'] = self.whereClause(args['edge_table'], args['geometry'], args['BBOX'])
        return """
            SELECT seq,
                id1 AS _path, id2 AS _node, id3 AS _edge, cost AS _cost FROM pgr_kdijkstraPath('
                SELECT %(id)s::int4 AS id,
                    %(source)s::int4 AS source,
                    %(target)s::int4 AS target,
                    %(cost)s::float8 AS cost%(reverse_cost)s
                    FROM %(edge_table)s
                    %(where_clause)s',
                %(source_id)s, array[%(target_ids)s], %(directed)s, %(has_reverse_cost)s)""" % args

    def getExportQuery(self, args):
        return self.getJoinResultWithEdgeTable(args)

    def getExportMergeQuery(self, args):
        args['result_query'] = self.getQuery(args)

        args['with_geom_query'] = """
            SELECT
              seq, _path,
              CASE
                WHEN result._node = %(edge_table)s.%(source)s
                  THEN %(edge_table)s.%(geometry)s
                ELSE ST_Reverse(%(edge_table)s.%(geometry)s)
              END AS path_geom
            FROM %(edge_table)s JOIN result
              ON %(edge_table)s.%(id)s = result._edge
            """ % args

        args['one_geom_query'] = """
            SELECT _path, ST_LineMerge(ST_Union(path_geom)) AS path_geom
            FROM with_geom
            GROUP BY _path
            ORDER BY _path
            """ % args

        args['aggregates_query'] = """SELECT
            _path,
            SUM(_cost) AS agg_cost,
            array_agg(_node ORDER BY seq) AS _nodes,
            array_agg(_edge ORDER BY seq) AS _edges
            FROM result
            GROUP BY _path
            """

        query = """
            WITH
            result AS ( %(result_query)s ),
            with_geom AS ( %(with_geom_query)s ),
            one_geom AS ( %(one_geom_query)s ),
            aggregates AS ( %(aggregates_query)s )
            SELECT row_number() over() as seq,
            _path, _nodes, _edges, agg_cost,
            path_geom FROM aggregates JOIN one_geom
            USING (_path)
            """ % args
        return query
        
# Draw the result.
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
                ## pgRouting <= 2.0.0rc1
                #query2 = """
                #    SELECT ST_AsText(%(transform_s)sST_Reverse(%(geometry)s)%(transform_e)s) FROM %(edge_table)s
                #        WHERE %(source)s = %(result_node_id)d AND %(id)s = %(result_edge_id)d
                #    UNION
                #    SELECT ST_AsText(%(transform_s)s%(geometry)s%(transform_e)s) FROM %(edge_table)s
                #        WHERE %(target)s = %(result_node_id)d AND %(id)s = %(result_edge_id)d;
                #""" % args
                ##Utils.logMessage(query2)
                cur2.execute(query2)
                row2 = cur2.fetchone()
                ##Utils.logMessage(str(row2[0]))
                assert row2, "Invalid result geometry. (path_id:%(result_path_id)d, node_id:%(result_node_id)d, edge_id:%(result_edge_id)d)" % args

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

    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
