# -*- coding: utf-8 -*-
# /*PGR-GNU*****************************************************************
# File: postgis.py
#
# Copyright (c) 2011~2019 pgRouting developers
# Mail: project@pgrouting.org
#
# Developer's GitHub nickname:
# - cayetanobv
# - AasheeshT
# - jef-n
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

from __future__ import print_function
from qgis.core import QgsDataSourceUri
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QInputDialog, QLineEdit
from psycopg2 import sql

import psycopg2
import psycopg2.extensions  # for isolation levels

from .. import dbConnection as DbConn
from .. import pgRoutingLayer_utils as Utils

# use unicode!
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)


class TableAttribute(DbConn.TableAttribute):
    def __init__(self, row):
        self.num, self.name, self.data_type, self.char_max_len, self.modifier, self.notnull, self.hasdefault, self.default = row


class TableConstraint(DbConn.TableConstraint):
    """ class that represents a constraint of a table (relation) """

    def __init__(self, row):
        self.name, con_type, self.is_defferable, self.is_deffered, keys = row[:5]
        self.keys = list(map(int, keys.split(' ')))
        self.con_type = TableConstraint.types[con_type]   # convert to enum
        if self.con_type == TableConstraint.TypeCheck:
            self.check_src = row[5]
        elif self.con_type == TableConstraint.TypeForeignKey:
            self.foreign_table = row[6]
            self.foreign_on_update = TableConstraint.on_action[row[7]]
            self.foreign_on_delete = TableConstraint.on_action[row[8]]
            self.foreign_match_type = TableConstraint.match_types[row[9]]
            self.foreign_keys = row[10]


class TableIndex(DbConn.TableIndex):
    def __init__(self, row):
        self.name, columns = row
        self.columns = list(map(int, columns.split(' ')))


class TableTrigger(DbConn.TableTrigger):
    def __init__(self, row):
        self.name, self.function, self.type, self.enabled = row


class TableRule(DbConn.TableRule):
    def __init__(self, row):
        self.name, self.definition = row


class DbError(DbConn.DbError):
    def __init__(self, error, query=None):
        msg = str(error.args[0])
        if query is None:
            if hasattr(error, "cursor") and hasattr(error.cursor, "query"):
                query = str(error.cursor.query)
        else:
            query = str(query)
        DbConn.DbError.__init__(self, msg, query)


class TableField(DbConn.TableField):
    def __init__(self, name, data_type, is_null=None, default=None, modifier=None):
        self.name, self.data_type, self.is_null, self.default, self.modifier = name, data_type, is_null, default, modifier


class Connection(DbConn.Connection):

    @classmethod
    def getTypeName(self):
        return 'postgis'

    @classmethod
    def getTypeNameString(self):
        return 'PostgreSQL'

    @classmethod
    def getProviderName(self):
        return 'postgres'

    @classmethod
    def getSettingsKey(self):
        return 'PostgreSQL'

    @classmethod
    def icon(self):
        return QIcon(":/icons/postgis_elephant.png")

    @classmethod
    def connect(self, selected, parent=None):
        settings = QSettings()
        settings.beginGroup(u"/%s/connections/%s" % (self.getSettingsKey(), selected))

        if not settings.contains("database"):  # non-existent entry?
            raise DbError('there is no defined database connection "%s".' % selected)

        get_value_str = lambda x: str(settings.value(x))
        service, host, port, database, username, password = list(map(get_value_str, ["service", "host", "port", "database", "username", "password"]))

        # qgis1.5 use 'savePassword' instead of 'save' setting
        isSave = settings.value("save")
        isSavePassword = settings.value("savePassword")
        if not (isSave or isSavePassword):
            (password, ok) = QInputDialog.getText(parent, "Enter password", 'Enter password for connection "%s":' % selected, QLineEdit.Password)
            if not ok: return

        settings.endGroup()

        uri = QgsDataSourceUri()
        if service:
            uri.setConnection(service, database, username, password)
        else:
            uri.setConnection(host, port, database, username, password)

        return Connection(uri)

    def __init__(self, uri):
        DbConn.Connection.__init__(self, uri)

        self.service = uri.service()
        self.host = uri.host()
        self.port = uri.port()
        self.dbname = uri.database()
        self.user = uri.username()
        self.passwd = uri.password()

        try:
            self.con = psycopg2.connect(self.connection_info(), connect_timeout=5)
        except psycopg2.OperationalError as e:
            raise DbError(e)

        if not self.dbname:
            self.dbname = self.current_database()

        self.has_spatial = self.check_spatial()

        self.check_geometry_columns_table()

        # a counter to ensure that the cursor will be unique
        self.last_cursor_id = 0

    def connection_info(self):
        """
            connection information in form of a string
        """
        con_str = ''
        if self.service: con_str += "service='%s' " % self.service
        if self.host: con_str += "host='%s' " % self.host
        if self.port: con_str += "port=%s " % self.port
        if self.dbname: con_str += "dbname='%s' " % self.dbname
        if self.user: con_str += "user='%s' " % self.user
        if self.passwd: con_str += "password='%s' " % self.passwd
        return con_str

    def current_database(self):
        """
            current_database()
        """
        c = self._exec_sql(sql.SQL("SELECT current_database()"))
        return c.fetchone()[0]

    def version(self):
        """
            version()
        """
        c = self._exec_sql(sql.SQL("SELECT version())"))
        return c.fetchone()[0]

    def check_spatial(self):
        """ check whether postgis_version is present in catalog """
        c = self._exec_sql(sql.SQL("SELECT COUNT(*) FROM pg_proc WHERE proname = 'postgis_version'"))
        return (c.fetchone()[0] > 0)

    def get_spatial_info(self):
        """ returns tuple about postgis support:
            - lib version
            - installed scripts version
            - released scripts version
            - geos version
            - proj version
            - whether uses stats
        """
        c = self._exec_sql(sql.SQL("""
            SELECT postgis_lib_version(), postgis_scripts_installed(), postgis_scripts_released(),
                postgis_geos_version(), postgis_proj_version(), postgis_uses_stats()"""))
        return c.fetchone()

    def check_geometry_columns_table(self):
        c = self._exec_sql(sql.SQL("""
            SELECT relname FROM pg_class
            WHERE relname = 'geometry_columns' AND pg_class.relkind IN ('v', 'r')"""))

        self.has_geometry_columns = (len(c.fetchall()) != 0)

        if not self.has_geometry_columns:
            self.has_geometry_columns_access = False
            return

        # find out whether has privileges to access geometry_columns table
        self.has_geometry_columns_access = self.get_table_privileges('geometry_columns')[0]

    def list_schemas(self):
        """
            get list of schemas in tuples: (oid, name, owner, perms)
            Not including schemas starting with pg_ or the information_schema
        """
        c = self._exec_sql(sql.SQL("""
            SELECT oid, nspname, pg_get_userbyid(nspowner), nspacl
            FROM pg_namespace
            WHERE nspname !~ '^pg_' AND nspname != 'information_schema'"""))

        schema_cmp = lambda x, y: -1 if x[1] < y[1] else 1

        return sorted(c.fetchall(), cmp=schema_cmp)

    def get_table_fields(self, table, schema=None):
        """
            return list of columns in table
        """
        schema_where = sql.SQL(" AND nspname={} ").format(sql.Literal) if schema is not None else ""
        c = self._exec_sql(sql.SQL("""
            SELECT a.attnum AS ordinal_position,
                a.attname AS column_name,
                t.typname AS data_type,
                a.attlen AS char_max_len,
                a.atttypmod AS modifier,
                a.attnotnull AS notnull,
                a.atthasdef AS hasdefault,
                adef.adsrc AS default_value
            FROM pg_class c
            JOIN pg_attribute a ON a.attrelid = c.oid
            JOIN pg_type t ON a.atttypid = t.oid
            JOIN pg_namespace nsp ON c.relnamespace = nsp.oid
            LEFT JOIN pg_attrdef adef ON adef.adrelid = a.attrelid AND adef.adnum = a.attnum
            WHERE
              c.relname = {0} {1} AND
                a.attnum > 0
            ORDER BY a.attnum""").format(sql.Literal(table), schema_where))

        attrs = []
        for row in c.fetchall():
            attrs.append(TableAttribute(row))
        return attrs

    def get_table_privileges(self, table, schema=None):
        """ table privileges: (select, insert, update, delete) """
        s, t = Utils.tableName(schema, table)
        c = self._exec_sql(sql.SQL("""SELECT has_table_privilege('{0}{1}','SELECT'),
                        has_table_privilege('{0}{1}', 'INSERT'),
                        has_table_privilege('{0}{1}', 'UPDATE'),
                        has_table_privilege('{0}{1}', 'DELETE')""").format(s, t))
        return c.fetchone()

    def _exec_sql(self, query):
        try:
            cursor = self.con.cursor()
            cursor.execute(query.as_string(self.con))
            return cursor
        except psycopg2.Error as e:
            # do the rollback to avoid a "current transaction aborted, commands ignored" errors
            self.con.rollback()
            raise DbError(e)
