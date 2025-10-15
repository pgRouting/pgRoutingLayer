# -*- coding: utf-8 -*-
# /*PGR-GNU*****************************************************************
# File: CostBase.py
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
from psycopg2 import sql
from .FunctionBase import FunctionBase


class CostBase(FunctionBase):

    def __init__(self, ui):
        FunctionBase.__init__(self, ui)

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
            result AS ( {result_query} ),
            departure AS (
                SELECT DISTINCT ON (start_vid, end_vid)
                       start_vid, end_vid,
                       CASE
                           WHEN {edge_table}.{source} = start_vid
                               THEN ST_StartPoint({edge_table}.{geometry})
                           ELSE ST_EndPoint({edge_table}.{geometry})
                       END AS depart
                FROM result
                JOIN {edge_schema}.{edge_table}
                  ON ({edge_table}.{source} = start_vid OR {edge_table}.{target} = start_vid)
                ORDER BY start_vid, end_vid, {edge_table}.{id}
            ),
            destination AS (
                SELECT DISTINCT ON (start_vid, end_vid)
                       start_vid, end_vid,
                       CASE
                           WHEN {edge_table}.{source} = end_vid
                               THEN ST_StartPoint({edge_table}.{geometry})
                           ELSE ST_EndPoint({edge_table}.{geometry})
                       END AS arrive
                FROM result
                JOIN {edge_schema}.{edge_table}
                  ON ({edge_table}.{source} = end_vid OR {edge_table}.{target} = end_vid)
                ORDER BY start_vid, end_vid, {edge_table}.{id}
            )

            SELECT result.*, ST_MakeLine(depart, arrive) AS path_geom

            FROM result
            JOIN departure USING (start_vid, end_vid)
            JOIN destination USING (start_vid, end_vid)
            """).format(**args)

    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        ''' draw the result '''
        self.drawCostPaths(rows, con, args, geomType, canvasItemList, mapCanvas)
