# -*- coding: utf-8 -*-
# /*PGR-GNU*****************************************************************
# File: drivingDistance.py
#
# Copyright (c) 2011~2019 pgRouting developers
# Mail: project@pgrouting.org
#
# Developer's GitHub nickname:
# - cayetanobv
# - AasheeshT
# - sanak
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
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import *
from qgis.core import QgsGeometry, QgsPointXY
from qgis.gui import QgsVertexMarker
from psycopg2 import sql
from pgRoutingLayer import pgRoutingLayer_utils as Utils
from .FunctionBase import FunctionBase


class Function(FunctionBase):
    # TODO fix completely

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'pgr_drivingDistance'

    @classmethod
    def getControlNames(self, version):
        ''' returns control names. '''
        if version < 2.1:
            # version 2.0 has only one to one
            return self.commonControls + self.commonBoxes + [
                'labelSourceId', 'lineEditSourceId', 'buttonSelectSourceId',
                'labelDistance', 'lineEditDistance',
            ]
        else:
            return self.commonControls + self.commonBoxes + [
                'labelSourceIds', 'lineEditSourceIds', 'buttonSelectSourceIds',
                'labelDistance', 'lineEditDistance',
            ]

    def prepare(self, canvasItemList):
        resultNodesVertexMarkers = canvasItemList['markers']
        for marker in resultNodesVertexMarkers:
            marker.setVisible(False)
        canvasItemList['markers'] = []

    def getQuery(self, args):
        ''' returns the sql query in required signature format of pgr_drivingDistance '''
        args['where_clause'] = self.whereClause(args['edge_table'], args['geometry'], args['BBOX'])
        if (args['version'] < 2.1):
            return sql.SQL("""
                SELECT seq, id1 AS _node, id2 AS _edge, cost AS _cost
                FROM pgr_drivingDistance('
                  SELECT %(id)s::int4 AS id,
                    %(source)s::int4 AS source,
                    %(target)s::int4 AS target,
                    %(cost)s::float8 AS cost%(reverse_cost)s
                  FROM %(edge_table)s
                  %(where_clause)s',
                  %(source_id)s, %(distance)s,
                  %(directed)s, %(has_reverse_cost)s)""").format(**args)

        # 2.1 or greater
        # TODO add equicost flag to gui
        return sql.SQL("""
                SELECT seq, '(' || from_v || ', %(distance)s)' AS path_name,
                    from_v AS _from_v,
                    node AS _node, edge AS _edge,
                    cost AS _cost, agg_cost as _agg_cost
                FROM pgr_drivingDistance('
                  SELECT %(id)s AS id,
                    %(source)s AS source,
                    %(target)s AS target,
                    %(cost)s AS cost%(reverse_cost)s
                  FROM %(edge_table)s
                  %(where_clause)s',
                  ARRAY[%(source_ids)s]::BIGINT[], %(distance)s,
                  %(directed)s, false)
                """).format(**args)

    def getExportQuery(self, args):
        # points are returned
        args['result_query'] = self.getQuery(args)

        args['with_geom_query'] = sql.SQL("""
            SELECT result.*,
               ST_X(the_geom) AS x, ST_Y(the_geom) AS y,
               the_geom AS path_geom
            FROM %(edge_table)s_vertices_pgr JOIN result
            ON %(edge_table)s_vertices_pgr.id = result._node
            """).format(**args)

        msgQuery = sql.SQL("""WITH
            result AS ( %(result_query)s ),
            with_geom AS ( %(with_geom_query)s )
            SELECT with_geom.*
            FROM with_geom
            ORDER BY seq
            """).format(**args)
        return msgQuery

    def getExportMergeQuery(self, args):
        # the set of edges of the spanning tree are returned
        return self.getJoinResultWithEdgeTable(args)

    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        ''' draw the result '''
        resultNodesVertexMarkers = canvasItemList['markers']
        schema = """%(edge_schema)s""" % args
        table = """%(edge_table)s_vertices_pgr""" % args
        srid, geomType = Utils.getSridAndGeomType(con, schema, table, 'the_geom')
        Utils.setTransformQuotes(args, srid, args['canvas_srid'])

        for row in rows:
            cur2 = con.cursor()
            if args['version'] < 2.1:
                args['result_node_id'] = row[1]
                args['result_edge_id'] = row[2]
                args['result_cost'] = row[3]
            else:
                args['result_node_id'] = row[3]
                args['result_edge_id'] = row[4]
                args['result_cost'] = row[5]

            query2 = sql.SQL("""
                    SELECT ST_AsText(%(transform_s)s the_geom %(transform_e)s)
                    FROM %(edge_table)s_vertices_pgr
                    WHERE  id = %(result_node_id)d
                    """).format(**args)
            cur2.execute(query2)
            row2 = cur2.fetchone()
            if (row2):
                geom = QgsGeometry().fromWkt(str(row2[0]))
                pt = geom.asPoint()
                vertexMarker = QgsVertexMarker(mapCanvas)
                vertexMarker.setColor(Qt.red)
                vertexMarker.setPenWidth(2)
                vertexMarker.setIconSize(5)
                vertexMarker.setCenter(QgsPointXY(pt))
                resultNodesVertexMarkers.append(vertexMarker)

    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
