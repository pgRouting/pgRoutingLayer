# -*- coding: utf-8 -*-
# /*PGR-GNU*****************************************************************
# File: DijkstraBase.py
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
from pgRoutingLayer import pgRoutingLayer_utils as Utils
from .FunctionBase import FunctionBase
from psycopg2 import sql


class DijkstraBase(FunctionBase):

    def __init__(self, ui):
        FunctionBase.__init__(self, ui)

    @classmethod
    def getControlNames(self, version):
        ''' returns control names. '''
        return self.commonControls + self.commonBoxes + [
            'labelSourceIds', 'lineEditSourceIds', 'buttonSelectSourceIds',
            'labelTargetIds', 'lineEditTargetIds', 'buttonSelectTargetIds']

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
            FROM {function}('
                {innerQuery}
                ',
                {source_ids}, {target_ids}, {directed})
            """).format(**args)

    def getExportQuery(self, args):
        return self.getJoinResultWithEdgeTable(args)

    def getExportMergeQuery(self, args):
        return self.getExportManySourceManyTargetMergeQuery(args)

    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        columns = [2, 5, 6]
        self.drawManyPaths(rows, columns, con, args, geomType, canvasItemList, mapCanvas)
