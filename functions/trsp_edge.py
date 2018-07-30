from __future__ import absolute_import
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from builtins import str
from qgis.core import Qgis, QgsGeometry, QgsWkbTypes
from qgis.gui import QgsRubberBand
import psycopg2
from pgRoutingLayer import pgRoutingLayer_utils as Utils
from .FunctionBase import FunctionBase

class Function(FunctionBase):
    
    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'trsp(edge)'
    
    @classmethod
    def getControlNames(self, version):
        ''' returns control names. '''
        return self.commonControls + self.commonBoxes + [
                'labelSourceId', 'lineEditSourceId', 'buttonSelectSourceId',
                'labelSourcePos', 'lineEditSourcePos',
                'labelTargetId', 'lineEditTargetId', 'buttonSelectTargetId',
                'labelTargetPos', 'lineEditTargetPos',
                'labelTurnRestrictSql', 'plainTextEditTurnRestrictSql' ]                       

    
    @classmethod
    def isEdgeBase(self):
        return True
    
    def prepare(self, canvasItemList):
        resultPathRubberBand = canvasItemList['path']
        resultPathRubberBand.reset(Utils.getRubberBandType(False))
    
    def getQuery(self, args):
        ''' returns the sql query in required signature format of pgr_trsp_edge '''
        args['where_clause'] = self.whereClause(args['edge_table'], args['geometry'], args['BBOX'])
        return """
            SELECT seq, id1 AS _node, id2 AS _edge, cost AS _cost FROM pgr_trsp('
              SELECT %(id)s::int4 AS id,
                %(source)s::int4 AS source, %(target)s::int4 AS target,
                %(cost)s::float8 AS cost%(reverse_cost)s
              FROM %(edge_table)s
              %(where_clause)s',
              %(source_id)s, %(source_pos)s, %(target_id)s, %(target_pos)s, %(directed)s, %(has_reverse_cost)s, %(turn_restrict_sql)s)""" % args
    
    def getExportQuery(self, args):
        args['result_query'] = 'result AS (' + self.getQuery(args) + ')'

        args['max_seq_query'] = 'max_seq AS (SELECT max(seq), min(seq) FROM result) '

        args['with_geom'] = """ with_geom AS (
                SELECT
                lead(_node) over(), result.*, %(edge_table)s.* 
                FROM %(edge_table)s JOIN result
                ON edge_table.id = result._edge ORDER BY result.seq)""" % args

        args['first_row_split'] = self.getRowSplit(args, 'first')
        args['last_row_split'] = self.getRowSplit(args, 'last')

        args['intermediate_rows'] = """ intermediate_rows AS (SELECT 
              CASE
                WHEN result._node = %(edge_table)s.%(source)s
                  THEN %(edge_table)s.%(geometry)s
                ELSE ST_Reverse(%(edge_table)s.%(geometry)s)
              END AS path_geom,
              lead(_node) over(), result.*, %(edge_table)s.*
            FROM %(edge_table)s JOIN result
            ON %(edge_table)s.%(id)s = result._edge
            WHERE seq not in ((select max FROM max_seq), (select min FROM max_seq))
            ORDER BY result.seq) """ % args

        return """
            WITH
            %(result_query)s,
            %(max_seq_query)s,
            %(with_geom)s,
            %(first_row_split)s,
            %(last_row_split)s,
            %(intermediate_rows)s,
            join_query AS ((SELECT * FROM first_row) UNION (SELECT * FROM last_row) UNION (SELECT * FROM intermediate_rows))
            SELECT * FROM join_query order by seq
            """ % args

    def getExportMergeQuery(self, args):
        args['result_query'] = 'result AS (' + self.getQuery(args) + ')'

        args['max_seq_query'] = 'max_seq AS (SELECT max(seq), min(seq) FROM result) '

        args['with_geom'] = """ with_geom AS (
                SELECT
                lead(_node) over(), result.*, %(edge_table)s.* 
                FROM %(edge_table)s JOIN result
                ON edge_table.id = result._edge ORDER BY result.seq)""" % args

        args['first_row_split'] = self.getRowSplit(args, 'first')
        args['last_row_split'] = self.getRowSplit(args, 'last')

        args['intermediate_rows'] = """ intermediate_rows AS (SELECT 
              CASE
                WHEN result._node = %(edge_table)s.%(source)s
                  THEN %(edge_table)s.%(geometry)s
                ELSE ST_Reverse(%(edge_table)s.%(geometry)s)
              END AS path_geom,
              lead(_node) over(), result.*, %(edge_table)s.*
            FROM %(edge_table)s JOIN result
            ON %(edge_table)s.%(id)s = result._edge
            WHERE seq not in ((select max FROM max_seq), (select min FROM max_seq))
            ORDER BY result.seq) """ % args

        return """
            WITH
            %(result_query)s,
            %(max_seq_query)s,
            %(with_geom)s,
            %(first_row_split)s,
            %(last_row_split)s,
            %(intermediate_rows)s,
            join_query AS ((SELECT * FROM first_row) UNION (SELECT * FROM last_row) UNION (SELECT * FROM intermediate_rows)),
            one_geom_query AS (
                SELECT ST_LineMerge(ST_Union(path_geom)) AS path_geom,
                1 AS seq,
                SUM(_cost) AS agg_cost,
                array_agg(_node ORDER BY seq) AS _nodes,
                array_agg(_edge ORDER BY seq) AS _edges
            FROM join_query)
            SELECT * FROM one_geom_query order by seq
            """ % args

    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        ''' draw the result '''
        resultPathRubberBand = canvasItemList['path']
        i = 0
        count = len(rows)
        for row in rows:
            query2 = ""
            cur2 = con.cursor()
            args['result_node_id'] = row[1]
            args['result_edge_id'] = row[2]
            args['result_cost'] = row[3]
            
            if i == 0 and args['result_node_id'] == -1:
                args['result_next_node_id'] = rows[i + 1][1]
                query2 = """
                    SELECT ST_AsText(%(transform_s)sST_Line_Substring(%(geometry)s, %(source_pos)s, 1.0)%(transform_e)s) FROM %(edge_table)s
                        WHERE %(target)s = %(result_next_node_id)s AND %(id)s = %(result_edge_id)s
                    UNION
                    SELECT ST_AsText(%(transform_s)sST_Line_Substring(ST_Reverse(%(geometry)s), 1.0 - %(source_pos)s, 1.0)%(transform_e)s) FROM %(edge_table)s
                        WHERE %(source)s = %(result_next_node_id)s AND %(id)s = %(result_edge_id)s;
                """ % args
            elif i == (count - 1) and ((args['result_edge_id'] == -1) or (str(args['result_edge_id']) == args['target_id'])):
                if args['result_edge_id'] != -1:
                    query2 = """
                        SELECT ST_AsText(%(transform_s)sST_Line_Substring(%(geometry)s, 0.0, %(target_pos)s)%(transform_e)s) FROM %(edge_table)s
                            WHERE %(source)s = %(result_node_id)s AND %(id)s = %(result_edge_id)s
                        UNION
                        SELECT ST_AsText(%(transform_s)sST_Line_Substring(ST_Reverse(%(geometry)s), 0.0, 1.0 - %(target_pos)s)%(transform_e)s) FROM %(edge_table)s
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
                        resultPathRubberBand.addPoint(pt)
            elif geom.wkbType() == QgsWkbTypes.LineString:
                for pt in geom.asPolyline():
                    resultPathRubberBand.addPoint(pt)
            
            i = i + 1
    
    def getRowSplit(self, args, which):
        # PRIVATE method
        # upper case for localy defined string values
        #lower case come from args
        local_args = {}
        local_args['WHICH'] = which
        local_args['geometry'] = args['geometry']
        if which == 'first':
            local_args['WHAT'] = 'lead'
            local_args['POSITION'] = """%(source_pos)s""" % args
            local_args['MINMAX'] = 'min'
            local_args['NODE'] = """%(target)s""" % args
        else:
            local_args['WHAT'] = '_node'
            local_args['POSITION'] = """%(target_pos)s""" % args
            local_args['MINMAX'] = 'max'
            local_args['NODE'] = """%(source)s""" % args

        query = """
            %(WHICH)s_row_split AS (
              SELECT CASE
                WHEN %(WHAT)s = %(NODE)s THEN
                    ST_split( ST_Snap( %(geometry)s, ST_LineInterpolatePoint(%(geometry)s,  %(POSITION)s), 0.00001),
                        ST_LineInterpolatePoint(%(geometry)s,  %(POSITION)s))
                ELSE
                    ST_reverse( ST_split( ST_Snap( %(geometry)s, ST_LineInterpolatePoint(%(geometry)s, %(POSITION)s), 0.00001),
                            ST_LineInterpolatePoint(%(geometry)s, %(POSITION)s)))    
                END AS line_geom,
                st_length(%(geometry)s) AS length,
                _cost
              FROM with_geom WHERE seq = (select %(MINMAX)s FROM max_seq) ),
            %(WHICH)s_row_dump AS (SELECT (st_dump(line_geom)).geom AS path_geom, length, _cost FROM  %(WHICH)s_row_split),
            %(WHICH)s_row_choose AS (SELECT path_geom FROM  %(WHICH)s_row_dump WHERE abs(_cost -  st_length(path_geom) / length) < 0.00001),
            %(WHICH)s_row AS (SELECT * FROM  %(WHICH)s_row_choose, with_geom WHERE seq = (select %(MINMAX)s FROM max_seq))
            """ % local_args
        return query

    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
