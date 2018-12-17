from qgis.core import QgsMessageLog, Qgis, QgsWkbTypes
from qgis.gui import QgsMapCanvas
from qgis.PyQt.QtCore import QVariant, QSettings
#from PyQt4.QtGui import *
import psycopg2
from psycopg2 import sql
import sip


def getSridAndGeomType(con, table, geometry):
    ''' retrieve Spatial Reference Id and geometry type, example 4326(WGS84) , Point '''

    args = {}
    args['table'] = table
    args['geometry'] = geometry
    cur = con.cursor()
    cur.execute(sql.SQL("""
        SELECT ST_SRID({geometry}), ST_GeometryType({geometry})
            FROM {table}
            LIMIT 1
        """).format(**args).as_string(con))
    row = cur.fetchone()
    return row[0], row[1]


def getTransformedGeom(srid, canvas_srid, geometry):
    '''
    gets transformed geometry to canvas srid
    srid - normal value
    canvas_srid, geometry - composed values
    '''
    if srid == 0:
        return sql.SQL("ST_SetSRID({}, {})").format(geometry, canvas_srid)
    else:
        return sql.SQL("ST_transform({}, {})").format(geometry, canvas_srid)

def setTransformQuotes(args, srid, canvas_srid):
    ''' Sets transformQuotes '''
    if srid > 0 and canvas_srid > 0:
        args['transform_s'] = sql.SQL("ST_Transform(")
        args['transform_e'] = sql.SQL(", {}").format(sql.Literal(canvas_srid))
    else:
        args['transform_s'] = sql.SQL("")
        args['transform_e'] = sql.SQL("")

def isSIPv2():
    '''Checks the version of SIP '''
    return sip.getapi('QVariant') > 1

def getStringValue(settings, key, value):
    ''' returns key and its corresponding value. example: ("interval",30). '''
    if isSIPv2():
        return settings.value(key, value, type=str)
    else:
        return settings.value(key, QVariant(value)).toString()

def getBoolValue(settings, key, value):
    ''' returns True if settings exist otherwise False. '''
    if isSIPv2():
        return settings.value(key, value, type=bool)
    else:
        return settings.value(key, QVariant(value)).toBool()

def getDestinationCrs(mapCanvas):
    ''' returns Coordinate Reference ID of map/overlaid layers. '''
    return mapCanvas.mapSettings().destinationCrs()

def getCanvasSrid(crs):
    ''' Returns SRID based on QGIS version. '''
    return crs.postgisSrid()

def createFromSrid(crs, srid):
    ''' Creates EPSG crs for QGIS version 1 or Creates Spatial reference system based of SRID for QGIS version 2. '''
    return crs.createFromSrid(srid)

def getRubberBandType(isPolygon):
    ''' returns RubberBandType as polygon or lineString '''
    if isPolygon:
        return QgsWkbTypes.PolygonGeometry
    else:
        return QgsWkbTypes.LineGeometry

def refreshMapCanvas(mapCanvas):
    '''  refreshes the mapCanvas , RubberBand is cleared. '''
    return mapCanvas.refresh()

def logMessage(message, level=Qgis.Info):
    QgsMessageLog.logMessage(message, 'pgRouting Layer', level)

def getNodeQuery(args, geomType):
    ''' returns a sql query to get nodes from a geometry. '''
    setStartPoint(geomType, args)
    setEndPoint(geomType, args)
    return """
        WITH node AS (
            SELECT id::int4,
                ST_X(%(geometry)s) AS x,
                ST_Y(%(geometry)s) AS y,
                %(geometry)s
                FROM (
                    SELECT %(source)s::int4 AS id,
                        %(startpoint)s AS %(geometry)s
                        FROM %(edge_table)s
                    UNION
                    SELECT %(target)s::int4 AS id,
                        %(endpoint)s AS %(geometry)s
                        FROM %(edge_table)s
                ) AS node
        )""" % args

def getPgrVersion(con):
    ''' returns version of PostgreSQL database. '''
    try:
        cur = con.cursor()
        cur.execute('SELECT version FROM pgr_version()')
        row = cur.fetchone()[0]
        versions =  ''.join([i for i in row if i.isdigit()])
        version = versions[0]
        if versions[1]:
            version += '.' + versions[1]
        return float(version)
    except psycopg2.DatabaseError as e:
        #database didn't have pgrouting
        return 0
    except SystemError as e:
        return 0

def get_innerQuery(args):
    return sql.SQL("""
        SELECT {id} AS id,
                {source} AS source,
                {target} AS target,
                {cost}::FLOAT AS cost,
                {reverse_cost}::FLOAT AS reverse_cost
            FROM {edge_table}
            {where_clause}
        """.replace("\\n", r"\n")).format(**args)

def get_innerQueryXY(args):
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

def get_closestVertexInfo(args):
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
