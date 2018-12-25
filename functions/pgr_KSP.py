from __future__ import absolute_import
from psycopg2 import sql
from .FunctionBase import FunctionBase

class Function(FunctionBase):

    minPGRversion = 2.1

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'pgr_KSP'

    @classmethod
    def getControlNames(self, version):
        ''' returns control names. '''
        return self.commonControls + self.commonBoxes + [
            'labelSourceId', 'lineEditSourceId', 'buttonSelectSourceId',
            'labelTargetId', 'lineEditTargetId', 'buttonSelectTargetId',
            'labelPaths', 'lineEditPaths',
            'checkBoxHeapPaths'
            ]

    def getQuery(self, args):
        ''' returns the sql query in required signature format of pgr_KSP '''
        return sql.SQL("""
            SELECT seq,
              '(' || {source_id} || ', ' ||  {target_id} || ')-' || path_id AS path_name,
              path_id AS _path_id,
              path_seq AS _path_seq,
              node AS _node,
              edge AS _edge,
              cost AS _cost
            FROM pgr_KSP(' {innerQuery} ',
                {source_id}, {target_id}, {Kpaths}, {directed}, {heap_paths})
            """).format(**args)

    def getExportQuery(self, args):
        return self.getJoinResultWithEdgeTable(args)


    def getExportMergeQuery(self, args):
        args['result_query'] = self.getQuery(args)
        return sql.SQL("""WITH
            result AS ( {result_query} ),
            with_geom AS (
                SELECT seq, result.path_name,
                CASE
                    WHEN result._node = et.{source}
                      THEN et.{geometry}
                    ELSE ST_Reverse(et.{geometry})
                END AS path_geom
                FROM {edge_table} AS et JOIN result ON et.{id} = result._edge
            ),
            one_geom AS (
                SELECT path_name, ST_LineMerge(ST_Union(path_geom)) AS path_geom
                FROM with_geom GROUP BY path_name ORDER BY path_name
            ),
            aggregates AS (
                SELECT
                path_name, _path_id,
                SUM(_cost) AS agg_cost,
                array_agg(_node ORDER BY _path_seq) AS _nodes,
                array_agg(_edge ORDER BY _path_seq) AS _edges
                FROM result
                GROUP BY path_name, _path_id
            )
            SELECT row_number() over() as seq,
            _path_id, path_name, _nodes, _edges, agg_cost, path_geom
            FROM aggregates JOIN one_geom USING (path_name) ORDER BY _path_id
        """).format(**args)


    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        ''' draw the result '''
        columns = [2, 4, 5]
        self.drawManyPaths(rows, columns, con, args, geomType, canvasItemList, mapCanvas)


    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
