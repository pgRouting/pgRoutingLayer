from .. import pgRoutingLayer_utils as Utils
from FunctionBase import FunctionBase

class Function(FunctionBase):

    version = 2.0

    @classmethod
    def getName(self):
        return 'bdDijkstra'

    @classmethod
    def getControlNames(self, version):
        self.version = version
        if self.version < 2.5:
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
        if self.version < 2.5:
            resultPathRubberBand = canvasItemList['path']
            resultPathRubberBand.reset(Utils.getRubberBandType(False))
        else:
            resultPathsRubberBands = canvasItemList['paths']
            for path in resultPathsRubberBands:
                path.reset(Utils.getRubberBandType(False))
            canvasItemList['paths'] = []


    def getQuery(self, args):
        args['where_clause'] = self.whereClause(args['edge_table'], args['geometry'], args['BBOX'])
        if self.version < 2.4:
            return """
                SELECT seq, id1 AS _node, id2 AS _edge, cost AS _cost
                FROM pgr_bdDijkstra('
                    SELECT %(id)s::int4 AS id,
                        %(source)s::int4 AS source,
                        %(target)s::int4 AS target,
                        %(cost)s::float8 AS cost
                        %(reverse_cost)s,
                    FROM %(edge_table)s
                    %(where_clause)s',
                    %(source_id)s::int4, %(target_id)s::int4, %(directed)s, %(has_reverse_cost)s)
            """ % args
        elif self.version == 2.4:
            return """
                SELECT seq, node AS _node, edge AS _edge, cost AS _cost, lead(agg_cost) over() AS _agg_cost
                FROM pgr_bdDijkstra('
                    SELECT %(id)s AS id,
                        %(source)s AS source,
                        %(target)s AS target,
                        %(cost)s AS cost
                        %(reverse_cost)s,
                    FROM %(edge_table)s
                    %(where_clause)s',
                    %(source_id)s::int4, %(target_id)s::int4, %(directed)s, %(has_reverse_cost)s)
            """ % args
        else:
            return """
                SELECT seq, '(' || start_vid || ',' || end_vid || ')' AS path_name,
                    path_seq AS _path_seq, start_vid AS _start_vid, end_vid AS _end_vid,
                    node AS _node, edge AS _edge, cost AS _cost, lead(agg_cost) over() AS _agg_cost
                FROM pgr_bdDijkstra('
                    SELECT %(id)s AS id,
                        %(source)s AS source,
                        %(target)s AS target,
                        %(cost)s AS cost
                        %(reverse_cost)s,
                    FROM %(edge_table)s
                    %(where_clause)s',
                    array[%(source_ids)s]::BIGINT[], array[%(target_ids)s]::BIGINT[], %(directed)s)
                """ % args

    def getExportQuery(self, args):
        return self.getJoinResultWithEdgeTable(args)

    def getExportMergeQuery(self, args):
        if self.version < 2.5:
            return self.getExportOneSourceOneTargetMergeQuery(args)
        else:
            return self.getExportManySourceManyTargetMergeQuery(args)


    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        if self.version < 2.5:
            self.drawOnePath(rows, con, args, geomType, canvasItemList, mapCanvas)
        else:
            self.drawManyPaths(rows, con, args, geomType, canvasItemList, mapCanvas)




    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
