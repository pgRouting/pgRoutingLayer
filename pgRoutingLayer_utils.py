# -*- coding: utf-8 -*-
# /*PGR-GNU*****************************************************************
# File: pgRoutingLayer_utils.py
#
# Copyright (c) 2011~2019 pgRouting developers
# Mail: project@pgrouting.org
#
# Developer's GitHub nickname:
# - AasheeshT
# - cayetanobv
# - sanak
# - cvvergara
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


from qgis.core import QgsMessageLog, Qgis, QgsWkbTypes
from qgis.PyQt.QtCore import QVariant
import psycopg2
from psycopg2 import sql
import sip


def getSridAndGeomType(con, schema, table, geometry):
    ''' retrieve Spatial Reference Id and geometry type, example 4326(WGS84) , Point '''

    args = {}
    args['schema'] = schema
    args['table'] = table
    args['geometry'] = geometry
    cur = con.cursor()
    cur.execute(sql.SQL("""
        SELECT ST_SRID({geometry}), ST_GeometryType({geometry})
            FROM {schema}.{table}
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
        args['transform_e'] = sql.SQL(", {})").format(sql.Literal(canvas_srid))
    else:
        args['transform_s'] = sql.SQL("")
        args['transform_e'] = sql.SQL("")


def getStringValue(settings, key, value):
    ''' returns key and its corresponding value. example: ("interval",30). '''
    return settings.value(key, value, type=str)


def getBoolValue(settings, key, value):
    ''' returns True if settings exist otherwise False. '''
    return settings.value(key, value, type=bool)


def getDestinationCrs(mapCanvas):
    ''' returns Coordinate Reference ID of map/overlaid layers. '''
    return mapCanvas.mapSettings().destinationCrs()


def getCanvasSrid(crs):
    ''' Returns SRID. '''
    return crs.postgisSrid()


def createFromSrid(crs, srid):
    ''' Creates Spatial reference system based of SRID. '''
    return crs.createFromProj(str(srid))


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


def getPgrVersion(con):
    ''' returns version of PostgreSQL database. '''
    try:
        cur = con.cursor()
        cur.execute('SELECT version FROM pgr_full_version()')
        row = cur.fetchone()[0]
        versions = ''.join([i for i in row if i.isdigit()])
        version = versions[0]
        if versions[1]:
            version += '.' + versions[1]
        return float(version)
    except psycopg2.DatabaseError:
        # database didn't have pgrouting
        return 0
    except SystemError:
        return 0


def tableName(schema, table):
    if not schema:
        return sql.SQL(""), sql.Identifier(table)
    else:
        return sql.SQL("{}.").format(sql.Identifier(schema)), sql.Identifier(table)
