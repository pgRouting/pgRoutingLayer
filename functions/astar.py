from __future__ import absolute_import
from pgRoutingLayer import pgRoutingLayer_utils as Utils
from .FunctionBase import FunctionBase
from psycopg2 import sql

class Function(FunctionBase):

    minPGRversion = 2.4

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'pgr_astar'

    @classmethod
    def getControlNames(self, version):
        ''' returns control names for this function. '''
        return self.commonControls + self.commonBoxes + self.astarControls + [
                'labelSourceIds', 'lineEditSourceIds', 'buttonSelectSourceIds',
                'labelTargetIds', 'lineEditTargetIds', 'buttonSelectTargetIds',
                ]

    def prepare(self, canvasItemList):
        resultPathsRubberBands = canvasItemList['paths']
        for path in resultPathsRubberBands:
            path.reset(Utils.getRubberBandType(False))
        canvasItemList['paths'] = []


    def getQuery(self, args):
        ''' returns the sql query in required signature format of pgr_astar '''
        return sql.SQL("""
            SELECT seq, '(' || start_vid || ',' || end_vid || ')' AS path_name,
                path_seq AS _path_seq, start_vid AS _start_vid, end_vid AS _end_vid,
                node AS _node, edge AS _edge, cost AS _cost, lead(agg_cost) over() AS _agg_cost
            FROM pgr_astar('
                {innerQuery}
                ',
                {source_ids}, {target_ids}, {directed})
            """).format(**args)

    def getExportQuery(self, args):
        return self.getJoinResultWithEdgeTable(args)

    def getExportMergeQuery(self, args):
        return self.getExportManySourceManyTargetMergeQuery(args)


    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        ''' draw the result. '''
        self.drawManyPaths(rows, con, args, geomType, canvasItemList, mapCanvas)

    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
