from __future__ import absolute_import
from qgis.PyQt.QtCore import *
from builtins import str
from qgis.PyQt.QtGui import QColor
from qgis.core import Qgis, QgsGeometry, QgsWkbTypes
from qgis.gui import QgsRubberBand
import psycopg2
from pgRoutingLayer import pgRoutingLayer_utils as Utils
from .FunctionBase import FunctionBase

class Function(FunctionBase):

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'trsp(via edges)'

    @classmethod
    def getControlNames(self, version):
        ''' returns control names. '''
        return self.commonControls + self.commonBoxes + [
            'labelIds', 'lineEditIds', 'buttonSelectIds',
            'labelPcts', 'lineEditPcts',
            'checkBoxDirected', 'checkBoxHasReverseCost',
            'labelTurnRestrictSql', 'plainTextEditTurnRestrictSql'
        ]

    @classmethod
    def isEdgeBase(self):
        return True

    @classmethod
    def canExport(self):
        return True

    @classmethod
    def canExportMerged(self):
        return True

    def isSupportedVersion(self, version):
        return version >= 2.1

    def prepare(self, canvasItemList):
        resultPathsRubberBands = canvasItemList['paths']
        for path in resultPathsRubberBands:
            path.reset(Utils.getRubberBandType(False))
        canvasItemList['paths'] = []

    def getQuery(self, args):
        ''' returns the sql query in required signature format of trsp_via_edges '''
        args['where_clause'] = self.whereClause(args['edge_table'], args['geometry'], args['BBOX'])
        return """
            SELECT seq, id1 AS _path, id2 AS _node, id3 AS _edge, cost as _cost FROM pgr_trspViaEdges('
              SELECT %(id)s::int4 AS id,
                %(source)s::int4 AS source, %(target)s::int4 AS target,
                %(cost)s::float8 AS cost%(reverse_cost)s
              FROM %(edge_table)s
              %(where_clause)s',
              ARRAY[%(ids)s]::integer[], ARRAY[%(pcts)s]::float8[],
              %(directed)s, %(has_reverse_cost)s, %(turn_restrict_sql)s)""" % args

    def getQueries(self, args):
        args['edge_data_q'] = """
        edge_data AS (
            SELECT
                unnest(ARRAY[%(ids)s::integer]) AS eid,
                unnest(ARRAY[%(pcts)s::float8]) AS fraction
        ),
        geom_data AS (
            SELECT row_number() over() AS seq,
                %(id)s, %(source)s, %(target)s, fraction,
                ST_LineSubstring(%(geometry)s, fraction, 1) as totarget,
                ST_Reverse(ST_LineSubstring(%(geometry)s, 0, fraction)) as tosource
            FROM %(edge_table)s JOIN edge_data ON (%(edge_table)s.%(id)s = edge_data.eid)
        )
        """ % args

        args['result_q'] = """
        result AS (
            SELECT seq, id1 AS _path, id2 AS _node, id3 AS _edge, cost as _cost
            FROM pgr_trspViaEdges(
                'SELECT gid::int4 AS id, source::int4 AS source, target::int4 AS target, cost_s::float8 AS cost, reverse_cost_s::float8 AS reverse_cost
                    FROM %(edge_table)s WHERE  %(edge_table)s.%(geometry)s && %(BBOX)s',
                (select array_agg(eid::integer) from edge_data),
                (select array_agg(fraction::float) from edge_data),
                %(directed)s, %(has_reverse_cost)s, %(turn_restrict_sql)s)
        )
        """ % args

        args['the_rest_q'] = """
        result1 AS (
            SELECT seq, _path, lead(_path) over (ORDER BY seq) AS nextpath,
            _node, lead(_node)  over(ORDER BY seq) AS nextnode, _edge, _cost FROM result
        ),
        result_geom AS (
            SELECT CASE
                 WHEN result1.nextnode = %(target)s
                    THEN %(geometry)s
                    ELSE ST_Reverse(%(geometry)s)
            END AS path_geom,
            result1.*
            FROM  %(edge_table)s JOIN result1 ON  %(id)s  = result1._edge ORDER BY result1.seq
        ),
        first_node AS (
            SELECT result1.seq, _node, nextnode, _edge, _cost,
            CASE WHEN result1.nextnode = geom_data.target THEN geom_data.totarget ELSE geom_data.tosource END AS path_geom
            FROM geom_data JOIN result1 ON geom_data.gid = result1._edge WHERE _node = -1
        ),
        uturn_node AS (
            SELECT result1.seq, _node, nextnode, _edge, _cost,
            CASE WHEN result1._node = geom_data.source THEN ST_MakeLine(ARRAY[ST_reverse(tosource), tosource]) ELSE ST_MakeLine(ARRAY[ST_reverse(totarget), totarget]) END AS path_geom
            FROM geom_data JOIN result1 ON (gid = _edge) WHERE _node = nextnode
        ),
        last_node AS (
            SELECT result1.seq, _node, nextnode, _edge, _cost,
            CASE
                 WHEN result1.nextnode = geom_data.target
                    THEN ST_Reverse(geom_data.totarget)
                    ELSE ST_reverse(geom_data.tosource)
            END AS path_geom
            FROM geom_data JOIN result1 ON geom_data.gid = result1._edge WHERE result1.seq = (select max(seq) from result1)
        ),
        normal_edge AS (
            SELECT *
            FROM result_geom
            WHERE _path = nextpath AND _node != -1 AND _node != nextnode AND seq != (select max(seq) from result)
        ),
        all_edges AS (
            SELECT seq, _node, _edge, _cost, path_geom FROM first_node
            UNION SELECT seq, _node, _edge, _cost, path_geom FROM last_node
            UNION SELECT seq, _node, _edge, _cost, path_geom FROM uturn_node
            UNION SELECT seq, _node, _edge, _cost, path_geom FROM normal_edge
        )
        """ % args


    def getExportQuery(self, args):
        self.getQueries(args)

        query = """
            WITH
            %(edge_data_q)s,
            %(result_q)s,
            %(the_rest_q)s
            SELECT
              all_edges.*, %(edge_table)s.*
            FROM %(edge_table)s JOIN all_edges
              ON %(edge_table)s.%(id)s = all_edges._edge ORDER BY all_edges.seq
            """ % args
        return query

    def getExportMergeQuery(self, args):
        self.getQueries(args)

        query = """
            WITH
            %(edge_data_q)s,
            %(result_q)s,
            %(the_rest_q)s
            SELECT 1 as seq,
                array_agg(_node) as _nodes,
                array_agg(_edge) as _edges,
                ST_makeLine(path_geom) AS path_geom from all_edges
            """ % args
        return query

    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        ''' draw the result '''
        resultPathsRubberBands = canvasItemList['paths']
        rubberBand = None
        cur_path_id = -1

        i = 0
        count = len(rows)
        ids = args['ids'].split(',')
        args['last_id'] = ids[len(ids) - 1]
        pcts = args['pcts'].split(',')
        pct_idx = 0
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

            query2 = ""
            if i < (count - 1):
                args['result_next_path_id'] = rows[i + 1][1]
                args['result_next_node_id'] = rows[i + 1][2]
                if args['result_next_path_id'] != args['result_path_id']:
                    pct_idx += 1
            elif i == (count - 1):
                pct_idx = len(pcts) - 1
            args['current_pct'] = pcts[pct_idx]

            if i == 0 and args['result_node_id'] == -1:
                query2 = """
                    SELECT ST_AsText(%(transform_s)sST_Line_Substring(%(geometry)s, %(current_pct)s, 1.0)%(transform_e)s) FROM %(edge_table)s
                        WHERE %(target)s = %(result_next_node_id)s AND %(id)s = %(result_edge_id)s
                    UNION
                    SELECT ST_AsText(%(transform_s)sST_Line_Substring(ST_Reverse(%(geometry)s), 1.0 - %(current_pct)s, 1.0)%(transform_e)s) FROM %(edge_table)s
                        WHERE %(source)s = %(result_next_node_id)s AND %(id)s = %(result_edge_id)s;
                """ % args
            elif i < (count - 1) and (args['result_path_id'] != args['result_next_path_id']) and (args['result_node_id'] == args['result_next_node_id']):
                # round trip case
                query2 = """
                    SELECT ST_AsText(ST_LineMerge(ST_Collect(ARRAY[
                    (
                        SELECT ST_AsText(%(transform_s)sST_Line_Substring(%(geometry)s, 0.0, %(current_pct)s)%(transform_e)s) FROM %(edge_table)s
                            WHERE %(source)s = %(result_node_id)s AND %(id)s = %(result_edge_id)s
                        UNION
                        SELECT ST_AsText(%(transform_s)sST_Line_Substring(ST_Reverse(%(geometry)s), 0.0, 1.0 - %(current_pct)s)%(transform_e)s) FROM %(edge_table)s
                            WHERE %(target)s = %(result_node_id)s AND %(id)s = %(result_edge_id)s
                    ),
                    (
                        SELECT ST_AsText(%(transform_s)sST_Reverse(ST_Line_Substring(%(geometry)s, 0.0, %(current_pct)s))%(transform_e)s) FROM %(edge_table)s
                            WHERE %(source)s = %(result_node_id)s AND %(id)s = %(result_edge_id)s
                        UNION
                        SELECT ST_AsText(%(transform_s)sST_Reverse(ST_Line_Substring(ST_Reverse(%(geometry)s), 0.0, 1.0 - %(current_pct)s))%(transform_e)s) FROM %(edge_table)s
                            WHERE %(target)s = %(result_node_id)s AND %(id)s = %(result_edge_id)s
                    )])));
                """ % args
            elif i == (count - 1) and ((args['result_edge_id'] == -1) or (str(args['result_edge_id']) == args['last_id'])):
                if args['result_edge_id'] != -1:
                    query2 = """
                        SELECT ST_AsText(%(transform_s)sST_Line_Substring(%(geometry)s, 0.0, %(current_pct)s)%(transform_e)s) FROM %(edge_table)s
                            WHERE %(source)s = %(result_node_id)s AND %(id)s = %(result_edge_id)s
                        UNION
                        SELECT ST_AsText(%(transform_s)sST_Line_Substring(ST_Reverse(%(geometry)s), 0.0, 1.0 - %(current_pct)s)%(transform_e)s) FROM %(edge_table)s
                            WHERE %(target)s = %(result_node_id)s AND %(id)s = %(result_edge_id)s;
                    """ % args
                else:
                    break
            else:
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

            i = i + 1

        if rubberBand:
            resultPathsRubberBands.append(rubberBand)
            rubberBand = None

    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
