from __future__ import absolute_import
from .FunctionBase import FunctionBase

class Function(FunctionBase):

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'with_Points'

    @classmethod
    def getControlNames(self, version):
        ''' returns control names. '''
        self.version = version
        if self.version < 2.1:
            # version 2.0 has only one to one
            return self.commonControls + self.commonBoxes + [
                    'labelSourceId', 'lineEditSourceId', 'buttonSelectSourceId',
                    'labelTargetId','labelSide','lineEditSide','lineEditEdge_id','labelFraction','lineEditFraction', 'lineEditPointsTable', 'lineEditTargetId','labelPid','lineEditPid','labelEdge_id', 'buttonSelectTargetId',
                    'labelEdge_id','labelSide'

                    ]
        else:
            return self.commonControls + self.commonBoxes + [
                    'labelSourceIds', 'lineEditSourceIds', 'buttonSelectSourceIds',
                    'labelTargetIds', 'lineEditPointsTable', 'label_pointsTable', 'lineEditTargetIds', 'buttonSelectTargetIds',
                    'labelSide','lineEditSide','lineEditEdge_id','labelEdge_id','labelFraction','lineEditFraction','labelPid','lineEditPid',
                    'labelDrivingSide','checkBoxLeft','checkBoxRight','checkBoxDetails'
                    ]


    @classmethod
    def isSupportedVersion(self, version):
        ''' Checks supported version '''
        # valid starting pgr v2.1
        return version >= 2.1


    @classmethod
    def canExportQuery(self):
        return False

    @classmethod
    def canExportMerged(self):
        return False



    def prepare(self, canvasItemList):
        resultNodesTextAnnotations = canvasItemList['annotations']
        for anno in resultNodesTextAnnotations:
            anno.setVisible(False)
        canvasItemList['annotations'] = []


    def getQuery(self, args):
        ''' returns the sql query in required signature format of pgr_withPoints '''
        args['where_clause'] = self.whereClause(args['edge_table'], args['geometry'], args['BBOX'])
        args['where_clause_with'] = self.whereClause(args['points_table'], args['geometry'], args['BBOX'])
        return """
            SELECT seq, path_seq AS path_seq,
                   start_vid AS _start_vid , end_vid AS _end_vid, node, cost AS _cost, lead(agg_cost) over() AS agg_cost
            FROM pgr_withPoints('
              SELECT %(id)s AS id,
                %(source)s AS source,
                %(target)s AS target,
                %(cost)s AS cost
                %(reverse_cost)s
                FROM %(edge_table)s
                %(where_clause)s
                ',
                'SELECT %(pid)s AS pid,
                %(edge_id)s AS edge_id,
                %(fraction)s AS fraction,
                %(side)s AS side
                FROM %(points_table)s
                %(where_clause_with)s',
              array[%(source_ids)s]::BIGINT[], array[%(target_ids)s]::BIGINT[], %(directed)s, '%(driving_side)s', %(details)s)
            """ % args

    def getExportQuery(self, args):
        return self.getJoinResultWithEdgeTable(args)


    def getExportMergeQuery(self, args):
        if self.version < 2.1:
            return self.getExportOneSourceOneTargetMergeQuery(args)
        else:
            return self.getExportManySourceManyTargetMergeQuery(args)



    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        ''' draw the result '''
        if self.version < 2.1:
            self.drawOnePath(rows, con, args, geomType, canvasItemList, mapCanvas)
        else:
            self.drawManyPaths(rows, con, args, geomType, canvasItemList, mapCanvas)



    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
