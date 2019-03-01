# -*- coding: utf-8 -*-
# /*PGR-GNU*****************************************************************
# File: dbConnection.py
#
# Copyright (c) 2011~2019 pgRouting developers
# Mail: project@pgrouting.org
#
# Developer's GitHub nickname:
# - AasheeshT
# - cayetanobv
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
from qgis.core import QgsDataSourceUri
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QAction


class ConnectionManager(object):

    SUPPORTED_CONNECTORS = ['postgis']
    MISSED_CONNECTORS = []

    @classmethod
    def initConnectionSupport(self):
        conntypes = ConnectionManager.SUPPORTED_CONNECTORS
        for c in conntypes:
            try:
                self.getConnection(c)
            except ImportError as e:
                module = e.args[0][len("No module named "):]
                ConnectionManager.SUPPORTED_CONNECTORS.remove(c)
                ConnectionManager.MISSED_CONNECTORS.append((c, module))

    @classmethod
    def getConnection(self, conntype, uri=None):
        if not self.isSupported(conntype):
            raise NotSupportedConnTypeException(conntype)

        # import the connector
        exec("from pgRoutingLayer.connectors import %s as connector" % conntype, globals(), globals())
        return connector.Connection(uri) if uri else connector.Connection

    @classmethod
    def isSupported(self, conntype):
        return conntype in ConnectionManager.SUPPORTED_CONNECTORS

    @classmethod
    def getAvailableConnections(self, conntypes=None):
        if conntypes is None:
            conntypes = ConnectionManager.SUPPORTED_CONNECTORS
        if not hasattr(conntypes, '__iter__'):
            conntypes = [conntypes]

        connections = []
        for c in conntypes:
            connection = self.getConnection(c)
            connections.extend(connection.getAvailableConnections())
        return connections


class NotSupportedConnTypeException(Exception):
    def __init__(self, conntype):
        self.msg = u"%s is not supported yet" % conntype

    def __str__(self):
        return self.msg.encode('utf-8')


class DbError(Exception):
    def __init__(self, errormsg, query=None):
        self.msg = str(errormsg)
        self.query = str(query) if query else None

    def __str__(self):
        msg = self.msg.encode('utf-8')
        if self.query:
            msg += "\nQuery:\n" + self.query.encode('utf-8')
        return msg


class Connection(object):

    def __init__(self, uri):
        self.uri = uri

    @classmethod
    def getTypeName(self):
        pass

    @classmethod
    def getTypeNameString(self):
        pass

    @classmethod
    def getProviderName(self):
        pass

    @classmethod
    def getSettingsKey(self):
        pass

    @classmethod
    def icon(self):
        pass

    @classmethod
    def getAvailableConnections(self):
        connections = []

        settings = QSettings()
        settings.beginGroup("/%s/connections" % self.getSettingsKey())
        keys = settings.childGroups()
        for name in keys:
            connections.append(Connection.ConnectionAction(name, self.getTypeName()))
        settings.endGroup()

        return connections

    def getURI(self):
        # returns a new QgsDataSourceUri instance
        return QgsDataSourceUri(self.uri.connectionInfo())

    def getAction(self, parent=None):
        return Connection.ConnectionAction(self.uri.database(), self.getTypeName(), parent)

    class ConnectionAction(QAction):
        def __init__(self, text, conntype, parent=None):
            self.type = conntype
            icon = ConnectionManager.getConnection(self.type).icon()
            QAction.__init__(self, icon, text, parent)

        def connect(self):
            selected = self.text()
            conn = ConnectionManager.getConnection(self.type).connect(selected, self.parent())

            # set as default in QSettings
            settings = QSettings()
            settings.setValue("/%s/connections/selected" % conn.getSettingsKey(), selected)

            return conn


class TableAttribute(object):
    pass


class TableConstraint(object):
    """ class that represents a constraint of a table (relation) """

    TypeCheck, TypeForeignKey, TypePrimaryKey, TypeUnique = list(range(4))
    types = {"c": TypeCheck, "f": TypeForeignKey, "p": TypePrimaryKey, "u": TypeUnique}
    on_action = {"a": "NO ACTION", "r": "RESTRICT", "c": "CASCADE", "n": "SET NULL", "d": "SET DEFAULT"}
    match_types = {"u": "UNSPECIFIED", "f": "FULL", "p": "PARTIAL"}


class TableIndex(object):
    pass


class TableTrigger(object):
    # Bits within tgtype (pg_trigger.h)
    TypeRow = (1 << 0)  # row or statement
    TypeBefore = (1 << 1)  # before or after
    # events: one or more
    TypeInsert = (1 << 2)
    TypeDelete = (1 << 3)
    TypeUpdate = (1 << 4)
    TypeTruncate = (1 << 5)


class TableRule(object):
    pass


class TableField(object):
    def is_null_txt(self):
        if self.is_null:
            return "NULL"
        else:
            return "NOT NULL"

    def field_def(self, db):
        """ return field definition as used for CREATE TABLE or ALTER TABLE command """
        data_type = self.data_type if (not self.modifier or self.modifier < 0) else "%s(%d)" % (self.data_type, self.modifier)
        txt = "%s %s %s" % (db._quote(self.name), data_type, self.is_null_txt())
        if self.default and len(self.default) > 0:
            txt += " DEFAULT %s" % self.default
        return txt
