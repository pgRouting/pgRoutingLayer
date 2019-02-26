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
            JOIN  {vertex_schema}.{vertex_table} AS a ON (start_vid = a.id)
            JOIN  {vertex_schema}.{vertex_table} AS b ON (end_vid = b.id)
            """).format(**args)

    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        ''' draw the result '''
        self.drawCostPaths(rows, con, args, geomType, canvasItemList, mapCanvas)
