# coding=utf-8
# -*- coding: utf-8 -*-
# /*PGR-GNU*****************************************************************
# File: pgr_queries.py
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

from psycopg2 import sql


def getNodeQuery(args, geomType):
    ''' returns a sql query to get nodes from a geometry. '''
    return sql.SQL("""
        WITH node AS (
            SELECT {id},
                ST_X({geometry}) AS x,
                ST_Y({geometry}) AS y,
                {geometry}
            FROM (
                SELECT {source} AS id, ST_StartPoint({geom_t}) AS _geom
                FROM {edge_schema}.{edge_table}
                    UNION
                SELECT {target}, ST_EndPoint({geom_t})
                FROM {edge_schema}.{edge_table}
                ) AS node
       )""").format(**args)


def getEdgesQuery(args):
    return sql.SQL("""
        SELECT {id} AS id,
            {source} AS source,
            {target} AS target,
            {cost}::FLOAT AS cost,
            {reverse_cost}::FLOAT AS reverse_cost
        FROM {edge_schema}.{edge_table} {where_clause}
        """.replace("\\n", r"\n")).format(**args)


def getEdgesQueryXY(args):
    return sql.SQL("""
        SELECT {id} AS id,
                {source} AS source,
                {target} AS target,
                {cost}::FLOAT AS cost,
                {reverse_cost}::FLOAT AS reverse_cost,
                {x1}::FLOAT AS x1,
                {y1}::FLOAT AS y1,
                {x2}::FLOAT AS x2,
                {y2}::FLOAT AS y2
        FROM {edge_schema}.{edge_table} {where_clause}
        """.replace("\\n", r"\n")).format(**args)

def getEndPoint(args, vertex_id):
    # Prefer source endpoint when available; otherwise fallback to target endpoint
    return sql.SQL("""
        SELECT COALESCE(
            (SELECT ST_StartPoint({geometry}) FROM {edge_schema}.{edge_table} WHERE {source} = {vid} ORDER BY {id} LIMIT 1),
            (SELECT ST_EndPoint({geometry}) FROM {edge_schema}.{edge_table} WHERE {target} = {vid} ORDER BY {id} LIMIT 1)
        )
    """.replace("\\n", r"\n")).format(**args, vid=vertex_id)

def getCostLine(args, departure, arrival):
    return sql.Composed([
        sql.SQL("SELECT ST_AsText("),
        args['transform_s'],
        sql.SQL("ST_MakeLine(("),
        getEndPoint(args, departure),
        sql.SQL("), ("),
        getEndPoint(args, arrival),
        sql.SQL("))"),
        args['transform_e'],
        sql.SQL(") AS line"),
    ])

def getMidPoint():
    return sql.SQL("SELECT ST_asText(ST_LineInterpolatePoint(ST_GeomFromText(%s),0.5))")

def get_closestVertexInfo(args):
    return sql.SQL("""
        WITH
        near_source AS(SELECT {source},
                ST_Distance(
                    ST_StartPoint({geom_t}),
                    ST_GeomFromText('POINT({x} {y})', {dbcanvas_srid})
                ) AS dist,
                ST_AsText(ST_StartPoint({geom_t})) AS point
                FROM {edge_schema}.{edge_table}
                WHERE  {geom_t} && {SBBOX} ORDER BY dist ASC LIMIT 1
        ),
        near_target AS(SELECT {target},
                ST_Distance(
                    ST_EndPoint({geom_t}),
                    ST_GeomFromText('POINT({x} {y})', {dbcanvas_srid})
                ) AS dist,
                ST_AsText(ST_EndPoint({geom_t}))
                FROM {edge_schema}.{edge_table}
                WHERE  {geom_t} && {SBBOX} ORDER BY dist ASC LIMIT 1
        ),
        the_union AS (
            SELECT * FROM near_source UNION SELECT * FROM near_target
        )
        SELECT {source}, dist, point
        FROM the_union
        ORDER BY dist ASC LIMIT 1
        """).format(**args)


def get_closestEdgeInfo(args):
    # Not sure this is correct but has the main idea
    return sql.SQL("""
        WITH point AS (
            SELECT ST_GeomFromText('POINT({x} {y})', {dbcanvas_srid}) AS geom
        )
        SELECT {id)s,
            ST_Distance( {geometry}, point.geom) AS dist,
            ST_AsText( {geom_t} ) AS wkt,
            ROUND(ST_Line_Locate_Point( {geometry} , point.geom)::numeric, {decimal_places}) AS pos,
            ST_AsText({transform_s)sST_Line_Interpolate_point({geometry},
            ROUND(ST_Line_Locate_Point({geometry}, point.geom)::numeric, {decimal_places})){transform_e}) AS pointWkt
            FROM {edge_schema}.{edge_table}, point
            WHERE ST_SetSRID('BOX3D({minx} {miny}, {maxx} {maxy})'::BOX3D, {srid})
                && {geometry} ORDER BY dist ASC LIMIT 1""").format(args)
