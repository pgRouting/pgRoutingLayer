# -*- coding: utf-8 -*-
# /*PGR-GNU*****************************************************************
# File: AstarBase.py
#
# Copyright (c) 2011~2019 pgRouting developers
# Mail: project@pgrouting.org
#
# Developer's GitHub nickname:
# - cayetanobv
# - cvvergara
# - anitagraser
# ------
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# ********************************************************************PGR-GNU*/

from __future__ import absolute_import
from .DijkstraBase import DijkstraBase
from psycopg2 import sql


class AstarBase(DijkstraBase):

    def __init__(self, ui):
        DijkstraBase.__init__(self, ui)

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
