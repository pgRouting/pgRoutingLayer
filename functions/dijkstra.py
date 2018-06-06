from __future__ import absolute_import
from .. import pgRoutingLayer_utils as Utils
from .FunctionBase import FunctionBase

class Function(FunctionBase):

    version = 2.0
    
    @classmethod
    def getName(self):
        return 'dijkstra'
    

    @classmethod
    def getControlNames(self, version):
        self.version = version
        if self.version < 2.1:
            # version 2.0 has only one to one
            return self.commonControls + self.commonBoxes + [
                    'labelSourceId', 'lineEditSourceId', 'buttonSelectSourceId',
                    'labelTargetId', 'lineEditTargetId', 'buttonSelectTargetId',
                    ]
        else:
            return self.commonControls + self.commonBoxes + [
                    'labelSourceIds', 'lineEditSourceIds', 'buttonSelectSourceIds',
                    'labelTargetIds', 'lineEditTargetIds', 'buttonSelectTargetIds',
                    ]

    
    def prepare(self, canvasItemList):
        if self.version < 2.1:
            resultPathRubberBand = canvasItemList['path']
            resultPathRubberBand.reset(Utils.getRubberBandType(False))
        else:
            resultPathsRubberBands = canvasItemList['paths']
            for path in resultPathsRubberBands:
                path.reset(Utils.getRubberBandType(False))
            canvasItemList['paths'] = []

    
    def getQuery(self, args):
        args['where_clause'] = self.whereClause(args['edge_table'], args['geometry'], args['BBOX'])
        if self.version < 2.1:
            return """
                SELECT seq, id1 AS _node, id2 AS _edge, cost AS _cost
                FROM pgr_dijkstra('
                    SELECT %(id)s::int4 AS id,
                        %(source)s::int4 AS source,
                        %(target)s::int4 AS target,
                        %(cost)s::float8 AS cost
                        %(reverse_cost)s
                    FROM %(edge_table)s
                    %(where_clause)s',
                    %(source_id)s, %(target_id)s, %(directed)s, %(has_reverse_cost)s)
                """ % args
        else:
            return """
                SELECT seq, '(' || start_vid || ',' || end_vid || ')' AS path_name,
                    path_seq AS _path_seq, start_vid AS _start_vid, end_vid AS _end_vid,
                    node AS _node, edge AS _edge, cost AS _cost, lead(agg_cost) over() AS _agg_cost
                FROM pgr_dijkstra('
                    SELECT %(id)s AS id,
                        %(source)s AS source,
                        %(target)s AS target,
                        %(cost)s AS cost
                        %(reverse_cost)s
                    FROM %(edge_table)s
                    %(where_clause)s',
                    array[%(source_ids)s]::BIGINT[], array[%(target_ids)s]::BIGINT[], %(directed)s)
                """ % args

    def getExportQuery(self, args):
        return self.getJoinResultWithEdgeTable(args)


    def getExportMergeQuery(self, args):
        if self.version < 2.1:
            return self.getExportOneSourceOneTargetMergeQuery(args)
        else:
            return self.getExportManySourceManyTargetMergeQuery(args)



    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        if self.version < 2.1:
            self.drawOnePath(rows, con, args, geomType, canvasItemList, mapCanvas)
        else:
            self.drawManyPaths(rows, con, args, geomType, canvasItemList, mapCanvas)




    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
