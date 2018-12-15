from __future__ import absolute_import
from pgRoutingLayer import pgRoutingLayer_utils as Utils
from .FunctionBase import FunctionBase
from psycopg2 import sql

class Function(FunctionBase):

    minPGRversion = 2.5

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'pgr_bdDijkstra'

    @classmethod
    def getControlNames(self, version):
        ''' returns control names. '''
        return self.commonControls + self.commonBoxes + [
                'labelSourceIds', 'lineEditSourceIds', 'buttonSelectSourceIds',
                'labelTargetIds', 'lineEditTargetIds', 'buttonSelectTargetIds',
                ]

    def prepare(self, canvasItemList):
        resultPathsRubberBands = canvasItemList['paths']
        for path in resultPathsRubberBands:
            path.reset(Utils.getRubberBandType(False))
        canvasItemList['paths'] = []


    @classmethod
    def getQuery(self, args, cur, conn):
        ''' returns the sql query in required signature format of pgr_bdDijkstra '''
        args['where_clause'] = self.whereClause(args['edge_table'], args['geometry'], args['BBOX'])
        args['innerQuery'] = sql.SQL("""
            SELECT {id} AS id,
                    {source} AS source,
                    {target} AS target,
                    {cost}
                    {reverse_cost}
                FROM {edge_table}
                {where_clause}
            """.replace("\\n", r"\n")).format(**args)

        cur.execute(sql.SQL("""
            SELECT seq, '(' || start_vid || ',' || end_vid || ')' AS path_name,
                path_seq AS _path_seq, start_vid AS _start_vid, end_vid AS _end_vid,
                node AS _node, edge AS _edge, cost AS _cost, lead(agg_cost) over() AS _agg_cost
            FROM pgr_bdDijkstra('
                {innerQuery}
                ',
                {source_ids}, {target_ids}, {directed})
            """).format(**args).as_string(conn))

    def getExportQuery(self, args):
        return self.getJoinResultWithEdgeTable(args)

    def getExportMergeQuery(self, args):
        return self.getExportManySourceManyTargetMergeQuery(args)


    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        ''' draw the result '''
        self.drawManyPaths(rows, con, args, geomType, canvasItemList, mapCanvas)

    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
