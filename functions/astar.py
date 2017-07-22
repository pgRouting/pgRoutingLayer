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
        return 'astar'
    
    @classmethod
    def getControlNames(self, version):
        self.version = version
        if self.version < 2.4:
            return self.commonControls + self.commonBoxes + self.astarControls + [
                    'labelSourceId', 'lineEditSourceId', 'buttonSelectSourceId',
                    'labelTargetId', 'lineEditTargetId', 'buttonSelectTargetId',
                    ]
        else:
            return self.commonControls + self.commonBoxes + self.astarControls + [
                    'labelSourceIds', 'lineEditSourceIds', 'buttonSelectSourceIds',
                    'labelTargetIds', 'lineEditTargetIds', 'buttonSelectTargetIds',
                    ]

    def prepare(self, canvasItemList):
        if self.version < 2.4:
            resultPathRubberBand = canvasItemList['path']
            resultPathRubberBand.reset(Utils.getRubberBandType(False))
        else:
            resultPathsRubberBands = canvasItemList['paths']
            for path in resultPathsRubberBands:
                path.reset(Utils.getRubberBandType(False))
            canvasItemList['paths'] = []

    
    def getQuery(self, args):
        args['where_clause'] = self.whereClause(args['edge_table'], args['geometry'], args['BBOX'])
        if self.version < 2.3:
            return """
            SELECT seq, id1 AS _node, id2 AS _edge, cost AS _cost FROM pgr_astar('
                SELECT %(id)s::int4 AS id,
                    %(source)s::int4 AS source,
                    %(target)s::int4 AS target,
                    %(cost)s::float8 AS cost%(reverse_cost)s,
                    %(x1)s::float8 AS x1,
                    %(y1)s::float8 AS y1,
                    %(x2)s::float8 AS x2,
                    %(y2)s::float8 AS y2
                    FROM %(edge_table)s
                    %(where_clause)s',
                %(source_id)s::int4, %(target_id)s::int4, %(directed)s, %(has_reverse_cost)s)""" % args
        elif self.version == 2.3:
            return """
            SELECT seq, node AS _node, edge AS _edge, cost AS _cost, lead(agg_cost) over() AS _agg_cost
                FROM pgr_astar('
                SELECT %(id)s AS id,
                    %(source)s AS source,
                    %(target)s AS target,
                    %(cost)s AS cost%(reverse_cost)s,
                    %(x1)s AS x1,
                    %(y1)s AS y1,
                    %(x2)s AS x2,
                    %(y2)s AS y2
                    FROM %(edge_table)s
                    %(where_clause)s',
                %(source_id)s::int4, %(target_id)s::int4, %(directed)s, %(has_reverse_cost)s)""" % args
        else:
            return """
            SELECT seq, '(' || start_vid || ',' || end_vid || ')' AS path_name,
                  path_seq AS _path_seq, start_vid AS _start_vid, end_vid AS _end_vid,
                  node AS _node, edge AS _edge, cost AS _cost, lead(agg_cost) over() AS _agg_cost
            FROM pgr_astar('
                SELECT %(id)s AS id,
                    %(source)s AS source,
                    %(target)s AS target,
                    %(cost)s AS cost%(reverse_cost)s,
                    %(x1)s AS x1,
                    %(y1)s AS y1,
                    %(x2)s AS x2,
                    %(y2)s AS y2
                    FROM %(edge_table)s
                    %(where_clause)s',
                array[%(source_ids)s]::BIGINT[], array[%(target_ids)s]::BIGINT[], %(directed)s)
            """ % args




    def getExportQuery(self, args):
        return self.getJoinResultWithEdgeTable(args)

    def getExportMergeQuery(self, args):
        if self.version < 2.4:
             return self.getExportOneSourceOneTargetMergeQuery(args)
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

            args['aggregates_query'] = """
                SELECT
                    path_name, _start_vid, _end_vid,
                    SUM(_cost) AS agg_cost,
                    array_agg(_node ORDER BY _path_seq) AS _nodes,
                    array_agg(_edge ORDER BY _path_seq) AS _edges
                    FROM result
                GROUP BY path_name, _start_vid, _end_vid
                ORDER BY _start_vid, _end_vid"""

            query = """WITH
                result AS ( %(result_query)s ),
                with_geom AS ( %(with_geom_query)s ),
                one_geom AS ( %(one_geom_query)s ),
                aggregates AS ( %(aggregates_query)s )
                SELECT row_number() over() as seq,
                    path_name, _start_vid, _end_vid, agg_cost, _nodes, _edges,
                    path_geom AS path_geom FROM aggregates JOIN one_geom
                    USING (path_name)
                """ % args

            return query




    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        if self.version < 2.1:
            resultPathRubberBand = canvasItemList['path']
            for row in rows:
                cur2 = con.cursor()
                args['result_node_id'] = row[1]
                args['result_edge_id'] = row[2]
                args['result_cost'] = row[3]
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
                    if geom.wkbType() == QGis.WKBMultiLineString:
                        for line in geom.asMultiPolyline():
                            for pt in line:
                                resultPathRubberBand.addPoint(pt)
                    elif geom.wkbType() == QGis.WKBLineString:
                        for pt in geom.asPolyline():
                            resultPathRubberBand.addPoint(pt)
        else:

            resultPathsRubberBands = canvasItemList['paths']
            rubberBand = None
            cur_path_id = str(-1) + "," + str(-1)
            for row in rows:
                cur2 = con.cursor()
                args['result_path_id'] = str(row[3]) + "," + str(row[4])
                args['result_node_id'] = row[5]
                args['result_edge_id'] = row[6]
                args['result_cost'] = row[7]
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
                    assert row2, "Invalid result geometry. (path_id:%(result_path_id)s, node_id:%(result_node_id)d, edge_id:%(result_edge_id)d)" % args

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
