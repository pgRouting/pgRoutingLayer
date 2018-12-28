from __future__ import absolute_import
from psycopg2 import sql
from .FunctionBase import FunctionBase

class CostBase(FunctionBase):

    @classmethod
    def isSupportedVersion(self, version):
        ''' Checks supported version '''
        # valid starting pgr v2.1
        return version >= 2.1


    @classmethod
    def canExportMerged(self):
        return False


    def prepare(self, canvasItemList):
        resultNodesTextAnnotations = canvasItemList['annotations']
        for anno in resultNodesTextAnnotations:
            anno.setVisible(False)
        canvasItemList['annotations'] = []


    def getQuery(self, args):
        ''' returns the sql query in required signature format of pgr_dijkstra '''
        return sql.SQL("""
            SELECT row_number() over() AS seq,
                   start_vid , end_vid, agg_cost AS cost,
                    '(' || start_vid || ',' || end_vid || ')' AS path_name
            FROM {function}('
                {innerQuery}
                ',
                {source_ids}, {target_ids}, {directed})
            """).format(**args)

    def getExportQuery(self, args):
        args['result_query'] = self.getQuery(args)

        return sql.SQL("""
            WITH
            result AS ( {result_query} )
            SELECT result.*, ST_MakeLine(a.the_geom, b.the_geom) AS path_geom

            FROM result
            JOIN  {vertex_table} AS a ON (start_vid = a.id)
            JOIN  {vertex_table} AS b ON (end_vid = b.id)
            """).format(**args)

    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        ''' draw the result '''
        self.drawCostPaths(rows, con, args, geomType, canvasItemList, mapCanvas)

    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
