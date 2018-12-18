from __future__ import absolute_import
from pgRoutingLayer import pgRoutingLayer_utils as Utils
from .FunctionBase import FunctionBase
from psycopg2 import sql

class DijkstraBase(FunctionBase):

    minPGRversion = 2.1

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'pgr_dijkstra'

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
    def getQuery(self, args):
        ''' returns the sql query in required signature format of pgr_dijkstra '''
        return sql.SQL("""
            SELECT seq, '(' || start_vid || ',' || end_vid || ')' AS path_name,
                path_seq AS _path_seq, start_vid AS _start_vid, end_vid AS _end_vid,
                node AS _node, edge AS _edge, cost AS _cost, lead(agg_cost) over() AS _agg_cost
            FROM pgr_dijkstra('
                {innerQuery}
                ',
                {source_ids}, {target_ids}, {directed})
            """).format(**args)

    def getExportQuery(self, args):
        return self.getJoinResultWithEdgeTable(args)

    def getExportMergeQuery(self, args):
        return self.getExportManySourceManyTargetMergeQuery(args)

    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        ''' draw the result '''
        self.drawManyPaths(rows, con, args, geomType, canvasItemList, mapCanvas)

    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
