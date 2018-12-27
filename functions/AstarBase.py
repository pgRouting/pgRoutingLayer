from __future__ import absolute_import
from .DijkstraBase import DijkstraBase
from psycopg2 import sql

class AstarBase(DijkstraBase):

    @classmethod
    def getControlNames(self, version):
        return self.commonControls + self.commonBoxes + self.astarControls + [
                'labelSourceIds', 'lineEditSourceIds', 'buttonSelectSourceIds',
                'labelTargetIds', 'lineEditTargetIds', 'buttonSelectTargetIds',
                ]

    @classmethod
    def getQuery(self, args):
        ''' returns the sql query in required signature format of pgr_dijkstra '''
        return sql.SQL("""
            SELECT seq, '(' || start_vid || ',' || end_vid || ')' AS path_name,
                path_seq AS _path_seq, start_vid AS _start_vid, end_vid AS _end_vid,
                node AS _node, edge AS _edge, cost AS _cost, lead(agg_cost) over() AS _agg_cost
            FROM {function}('
                {innerQuery}
                ',
                {source_ids}, {target_ids}, {directed},
                heuristic := {astarHeuristic},
                factor := {astarFactor},
                epsilon := {astarEpsilon})
            """).format(**args)

    def __init__(self, ui):
        DijkstraBase.__init__(self, ui)
