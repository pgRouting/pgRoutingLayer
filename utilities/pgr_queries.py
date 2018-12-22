from qgis.core import QgsMessageLog, Qgis, QgsWkbTypes
from qgis.PyQt.QtCore import QVariant
import psycopg2
from psycopg2 import sql
import sip

"""
For pgRouting queries
"""


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
                FROM {edge_table}
                    UNION
                SELECT {target}, ST_EndPoint({geom_t})
                FROM {edge_table}
                ) AS node
       )""").format(**args)

def getEdgesQuery(args):
    return sql.SQL("""
        SELECT {id} AS id,
                {source} AS source,
                {target} AS target,
                {cost}::FLOAT AS cost,
                {reverse_cost}::FLOAT AS reverse_cost
            FROM {edge_table}
            {where_clause}
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
            FROM {edge_table}
            {where_clause}
        """.replace("\\n", r"\n")).format(**args)

    return  sql.SQL("""
        WITH
        near_source AS(SELECT {source},
                ST_Distance(
                    ST_StartPoint({geom_t}),
                    ST_GeomFromText('POINT({x} {y})', {dbcanvas_srid})
                ) AS dist,
                ST_AsText(ST_StartPoint({geom_t})) AS point
                FROM {edge_table}
                WHERE  {geom_t} && {SBBOX} ORDER BY dist ASC LIMIT 1
        ),
        near_target AS(SELECT {target},
                ST_Distance(
                    ST_EndPoint({geom_t}),
                    ST_GeomFromText('POINT({x} {y})', {dbcanvas_srid})
                ) AS dist,
                ST_AsText(ST_EndPoint({geom_t}))
                FROM {edge_table}
                WHERE  {geom_t} && {SBBOX} ORDER BY dist ASC LIMIT 1
        ),
        the_union AS (
            SELECT * FROM near_source UNION SELECT * FROM near_target
        )
        SELECT {source}, dist, point
        FROM the_union
        ORDER BY dist ASC LIMIT 1
        """).format(**args)
