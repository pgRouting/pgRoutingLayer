# coding=utf-8
# -*- coding: utf-8 -*-
# /*PGR-GNU*****************************************************************
# File: qgis_models.py
# 
# Copyright (c) 2011~2019 pgRouting developers
# Mail: project@pgrouting.org
# 
# Developer's GitHub nickname: 
# - cayetanobv
# - AasheeshT 
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

import unittest
import FunctionBase as FB


class TestFB(unittest.TestCase):
    def test_getJoinResultWithEdgeTable(self):
        args = {
            'geometry': 'test_geom', 'source': 'test_source', 'startpoint': 10,
            'id': 'test_id', 'edge_table': 'test_Table', 'target': 100, 'endpoint': 90
        }

        expected_sql = """
            WITH
            result AS (  )
            SELECT
              CASE
                WHEN result._node = test_Table.test_source
                  THEN test_Table.test_geom
                ELSE ST_Reverse(test_Table.test_geom)
              END AS path_geom,
              result.*, test_Table.*
            FROM test_Table JOIN result
              ON test_Table.test_id = result._edge ORDER BY result.seq
            """
        self.maxDiff = None

        self.assertEqual(FB.getJoinResultWithEdgeTable(args), expected_sql)

    def test_getExportManySourceManyTargetMergeQuery(self):

        args = {
            'geometry': 'test_geom', 'source': 'test_source', 'startpoint': 10,
            'id': 'test_id', 'edge_table': 'test_Table', 'target': 100, 'endpoint': 90
        }

        expected_sql = """WITH
            result AS (  ),
            with_geom AS (
            SELECT
              seq, result.path_name,
              CASE
                WHEN result._node = test_Table.test_source
                  THEN test_Table.test_geom
                ELSE ST_Reverse(test_Table.test_geom)
              END AS path_geom
            FROM test_Table JOIN result
              ON test_Table.test_id = result._edge
             ),
            one_geom AS (
            SELECT path_name, ST_LineMerge(ST_Union(path_geom)) AS path_geom
            FROM with_geom
            GROUP BY path_name
            ORDER BY path_name
             ),
            aggregates AS (
                SELECT
                    path_name, _start_vid, _end_vid,
                    SUM(_cost) AS agg_cost,
                    array_agg(_node ORDER BY _path_seq) AS _nodes,
                    array_agg(_edge ORDER BY _path_seq) AS _edges
                    FROM result
                GROUP BY path_name, _start_vid, _end_vid
                ORDER BY _start_vid, _end_vid )
            SELECT row_number() over() as seq,
                path_name, _start_vid, _end_vid, agg_cost, _nodes, _edges,
                path_geom AS path_geom FROM aggregates JOIN one_geom
                USING (path_name)
            """
        self.maxDiff = None

        self.assertEqual(FB.getExportManySourceManyTargetMergeQuery(args), expected_sql)


if __name__ == '__main__':

    unittest.main()
