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
