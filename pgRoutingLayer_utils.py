from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import psycopg2       # used for interacting with PostgreSQL
import sip            # used to create python bindings for C/C++ libraries


def getSridAndGeomType(con, table, geometry):   # retrieve Spatial Reference Id and geometry type, example 4326(WGS84) , Point
    args = {}
    args['table'] = table
    args['geometry'] = geometry
    cur = con.cursor() # cur is a cursor made on database connection 'con' to execute sql query
    cur.execute("""
        SELECT ST_SRID(%(geometry)s), ST_GeometryType(%(geometry)s)
            FROM %(table)s
            LIMIT 1
    """ % args)
    row = cur.fetchone()
    return row[0], row[1]


def setStartPoint(geomType, args):  # records startpoint of geometry and stores in args dictionary.
    if geomType == 'ST_MultiLineString':
        args['startpoint'] = "ST_StartPoint(ST_GeometryN(%(geometry)s, 1))" % args
# ST_GeometryN returns first linestring from a collection of linestrings and then ST_StartPoint gives startpoint for that line.

    elif geomType == 'ST_LineString':
        args['startpoint'] = "ST_StartPoint(%(geometry)s)" % args
        # ST_StartPoint returns the first point of a linestring.


def setEndPoint(geomType, args): # records endpoint and stores in args.
    if geomType == 'ST_MultiLineString':
        args['endpoint'] = "ST_EndPoint(ST_GeometryN(%(geometry)s, 1))" % args
        # ST_GeometryN returns first linestring from a collection of linestrings and then ST_EndPoint gives Endpoint.
    elif geomType == 'ST_LineString':
        args['endpoint'] = "ST_EndPoint(%(geometry)s)" % args
        # ST_StartPoint returns the first point of a linestring.

def setTransformQuotes(args, srid, canvas_srid):
    if srid > 0 and canvas_srid > 0:
        args['transform_s'] = "ST_Transform("
        args['transform_e'] = ", %(canvas_srid)d)" % args
    else:
        args['transform_s'] = ""
        args['transform_e'] = ""

def isSIPv2(): #Checks the version of SIP
    return sip.getapi('QVariant') > 1  # returns True when SIP version is 2 or more.


# settings are used to remember settings across sessions,stored in key-value pair.
def getStringValue(settings, key, value): # returns key and its corresponding value. example: ("interval",30).
    if isSIPv2():
        return settings.value(key, value, type=str)
    else:
        return settings.value(key, QVariant(value)).toString()

def getBoolValue(settings, key, value): #returns True if settings exist otherwise False.
    if isSIPv2():
        return settings.value(key, value, type=bool)
    else:
        return settings.value(key, QVariant(value)).toBool()

def isQGISv1():                         # returns True if QGis has version l.9 or less, otherwise False.
    return QGis.QGIS_VERSION_INT < 10900

# QGIS Uses 3 different ids for every reference system.
def getDestinationCrs(mapCanvas):       # returns Coordinate Reference ID of map/overlaid layers.
    if isQGISv1():
        return mapCanvas.mapRenderer().destinationSrs()
    else:
        if QGis.QGIS_VERSION_INT < 20400:
            return mapCanvas.mapRenderer().destinationCrs()
        else:
            return mapCanvas.mapSettings().destinationCrs()

def getCanvasSrid(crs): # Returns SRID based on QGIS version.
    if isQGISv1():
        return crs.epsg()  # Returns Id assigned by EPSG organisation.
    else:
        return crs.postgisSrid() # Returns SRID used by PostGIS.


def createFromSrid(crs, srid): # Returns True if CRS is created, otherwise false.
    if isQGISv1():
        return crs.createFromEpsg(srid)  # Creates EPSG crs for QGIS version 1.
    else:
        return crs.createFromSrid(srid)  # Creates Spatial reference system based of SRID for QGIS version 2.


# 'isPolygon' is true for (multi-)polygon, false for (multi-)linestring.
# RubberBand is a canvas item for drawing polygons and lines.
def getRubberBandType(isPolygon):
    if isQGISv1():
        return isPolygon
    else:
        if isPolygon:
            return QGis.Polygon   # returns RubberBandType as polygon
        else:
            return QGis.Line      # returns RubberBandType as linestring.

def refreshMapCanvas(mapCanvas):  # refreshes the mapCanvas , RubberBand is cleared.
    if QGis.QGIS_VERSION_INT < 20400:
        return mapCanvas.clear()
    else:
        return mapCanvas.refresh()

def logMessage(message, level=QgsMessageLog.INFO):
    QgsMessageLog.logMessage(message, 'pgRouting Layer', level)

def getNodeQuery(args, geomType): # returns a string which will be parameterised in a sql query to get nodes from a geometry.
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

def getPgrVersion(con):      # returns version of PostgreSQL database.
    try:
        cur = con.cursor()
        cur.execute('SELECT version FROM pgr_version()')
        row = cur.fetchone()[0]
        versions =  ''.join([i for i in row if i.isdigit()])
        version = versions[0]
        if versions[1]:
            version += '.' + versions[1]
        return float(version)
    except psycopg2.DatabaseError, e:
        #database didn't have pgrouting
        return 0;
    except SystemError, e:
        return 0
