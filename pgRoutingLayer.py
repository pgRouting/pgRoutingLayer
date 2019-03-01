# -*- coding: utf-8 -*-
# /*PGR-GNU*****************************************************************
# File: pgRoutingLayer.py
#
# Copyright (c) 2011~2019 pgRouting developers
# Mail: project@pgrouting.org
#
# Developer's GitHub nickname:
# - AasheeshT
# - cayetanobv
# - sanak
# - veniversum
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
# Import the PyQt and QGIS libraries
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QRegExp, QSettings, QUrl
from qgis.PyQt.QtGui import QColor, QIcon, QIntValidator, QDoubleValidator, QRegExpValidator, QCursor
from qgis.PyQt.QtWidgets import QAction, QApplication, QMessageBox
from qgis.core import QgsRectangle, QgsCoordinateReferenceSystem, QgsCoordinateTransform
from qgis.core import QgsProject, QgsGeometry, QgsWkbTypes
from qgis.gui import QgsVertexMarker, QgsRubberBand, QgsMapToolEmitPoint
from pgRoutingLayer import dbConnection
from pgRoutingLayer import pgRoutingLayer_utils as Utils
from pgRoutingLayer.utilities import pgr_queries as PgrQ
import os
import psycopg2
from psycopg2 import sql
import re
from PyQt5.QtGui import QDesktopServices

conn = dbConnection.ConnectionManager()


class PgRoutingLayer:

    SUPPORTED_FUNCTIONS = [

        'pgr_aStar',
        'pgr_aStarCost',
        'pgr_bdAstar',
        'pgr_bdAstarCost',
        'pgr_bdDijkstra',
        'pgr_bdDijkstraCost',
        'pgr_dijkstra',
        'pgr_dijkstraCost',
        'pgr_KSP',
    ]

    TOGGLE_CONTROL_NAMES = [
        'labelId', 'lineEditId',
        'labelSource', 'lineEditSource',
        'labelTarget', 'lineEditTarget',
        'labelCost', 'lineEditCost',
        'labelReverseCost', 'lineEditReverseCost',

        'labelX1', 'lineEditX1',
        'labelY1', 'lineEditY1',
        'labelX2', 'lineEditX2',
        'labelY2', 'lineEditY2',
        'labelAstarHeuristic', 'selectAstarHeuristic',
        'labelAstarFactor', 'selectAstarFactor',
        'labelAstarEpsilon', 'selectAstarEpsilon', 'showAstarEpsilon',

        # 'labelRule', 'lineEditRule',
        # 'labelToCost', 'lineEditToCost',
        'labelIds', 'lineEditIds', 'buttonSelectIds',
        'labelPcts', 'lineEditPcts',
        'labelSourceId', 'lineEditSourceId', 'buttonSelectSourceId',
        'labelSourceIds', 'lineEditSourceIds', 'buttonSelectSourceIds',
        'labelSourcePos', 'lineEditSourcePos',
        'labelTargetId', 'lineEditTargetId', 'buttonSelectTargetId',
        'labelTargetIds', 'lineEditTargetIds', 'buttonSelectTargetIds',
        'labelTargetPos', 'lineEditTargetPos',
        'labelDistance', 'lineEditDistance',
        'labelAlpha', 'lineEditAlpha',
        'labelPaths', 'lineEditPaths',
        'checkBoxDirected',
        'checkBoxHasReverseCost',
        'checkBoxHeapPaths',
        'checkBoxUseBBOX',
        'labelTurnRestrictSql', 'plainTextEditTurnRestrictSql',
        # 'checkBoxDetails',
        # 'label_pointsTable','lineEditPointsTable',
        # 'labelPid', 'lineEditPid', 'labelEdge_id', 'lineEditEdge_id',
        # 'labelFraction', 'lineEditFraction', 'labelSide', 'lineEditSide','labelDrivingSide','checkBoxLeft','checkBoxRight'
    ]

    ASTAR_HEURISTICS = [
        '= 0',
        '= abs(max(dx, dy))',
        '= abs(min(dx, dy))',
        '= dx * dx + dy * dy',
        '= sqrt(dx * dx + dy * dy)',
        '= abs(dx) + abs(dy)',
    ]

    FIND_RADIUS = 10
    FRACTION_DECIMAL_PLACES = 2
    version = 2.6
    functions = {}

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface

        self.idsVertexMarkers = []
        self.targetIdsVertexMarkers = []
        self.sourceIdsVertexMarkers = []
        self.sourceIdVertexMarker = QgsVertexMarker(self.iface.mapCanvas())
        self.sourceIdVertexMarker.setColor(Qt.blue)
        self.sourceIdVertexMarker.setPenWidth(2)
        self.sourceIdVertexMarker.setVisible(False)
        self.targetIdVertexMarker = QgsVertexMarker(self.iface.mapCanvas())
        self.targetIdVertexMarker.setColor(Qt.green)
        self.targetIdVertexMarker.setPenWidth(2)
        self.targetIdVertexMarker.setVisible(False)
        self.idsRubberBands = []
        self.sourceIdRubberBand = QgsRubberBand(self.iface.mapCanvas(), Utils.getRubberBandType(False))
        self.sourceIdRubberBand.setColor(Qt.cyan)
        self.sourceIdRubberBand.setWidth(4)
        self.targetIdRubberBand = QgsRubberBand(self.iface.mapCanvas(), Utils.getRubberBandType(False))
        self.targetIdRubberBand.setColor(Qt.yellow)
        self.targetIdRubberBand.setWidth(4)

        self.canvasItemList = {}
        self.canvasItemList['markers'] = []
        self.canvasItemList['annotations'] = []
        self.canvasItemList['paths'] = []
        resultPathRubberBand = QgsRubberBand(self.iface.mapCanvas(), Utils.getRubberBandType(False))
        resultPathRubberBand.setColor(QColor(255, 0, 0, 128))
        resultPathRubberBand.setWidth(4)
        self.canvasItemList['path'] = resultPathRubberBand
        resultAreaRubberBand = QgsRubberBand(self.iface.mapCanvas(), Utils.getRubberBandType(True))
        resultAreaRubberBand.setColor(Qt.magenta)
        resultAreaRubberBand.setWidth(2)
        resultAreaRubberBand.setBrushStyle(Qt.Dense4Pattern)
        self.canvasItemList['area'] = resultAreaRubberBand

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(QIcon(":/plugins/pgRoutingLayer/icon.png"), "pgRouting Layer", self.iface.mainWindow())
        # Add toolbar button and menu item
        self.iface.addPluginToDatabaseMenu("&pgRouting Layer", self.action)

        # load the form
        path = os.path.dirname(os.path.abspath(__file__))
        self.dock = uic.loadUi(os.path.join(path, "ui_pgRoutingLayer.ui"))
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

        self.idsEmitPoint = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.sourceIdEmitPoint = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.targetIdEmitPoint = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.sourceIdsEmitPoint = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.targetIdsEmitPoint = QgsMapToolEmitPoint(self.iface.mapCanvas())

        # connect the action to each method
        self.action.triggered.connect(self.show)
        self.dock.buttonReloadConnections.clicked.connect(self.reloadConnections)
        self.dock.comboConnections.currentIndexChanged.connect(self.updateConnectionEnabled)
        self.dock.comboBoxFunction.currentIndexChanged.connect(self.updateFunctionEnabled)

        self.dock.buttonSelectIds.clicked.connect(self.selectIds)
        self.idsEmitPoint.canvasClicked.connect(self.setIds)

        # One source id can be selected in some functions/version
        self.dock.buttonSelectSourceId.clicked.connect(self.selectSourceId)
        self.sourceIdEmitPoint.canvasClicked.connect(self.setSourceId)

        self.dock.buttonSelectTargetId.clicked.connect(self.selectTargetId)
        self.targetIdEmitPoint.canvasClicked.connect(self.setTargetId)

        # Function help
        self.dock.buttonFunctionHelp.clicked.connect(self.openHelp)

        # More than one source id can be selected in some functions/version
        self.dock.buttonSelectSourceIds.clicked.connect(self.selectSourceIds)
        self.sourceIdsEmitPoint.canvasClicked.connect(self.setSourceIds)

        self.dock.buttonSelectTargetIds.clicked.connect(self.selectTargetIds)
        self.targetIdsEmitPoint.canvasClicked.connect(self.setTargetIds)

        self.dock.checkBoxHasReverseCost.stateChanged.connect(self.updateReverseCostEnabled)

        self.dock.buttonRun.clicked.connect(self.run)
        self.dock.buttonExport.clicked.connect(self.export)
        self.dock.buttonExportMerged.clicked.connect(self.exportMerged)
        self.dock.buttonClear.clicked.connect(self.clear)

        self.prevType = None
        self.functions = {}
        for funcfname in self.SUPPORTED_FUNCTIONS:
            # import the function
            exec("from pgRoutingLayer.functions import %s as function" % funcfname, globals(), globals())
            funcname = function.Function.getName()
            self.functions[funcname] = function.Function(self.dock)
            self.dock.comboBoxFunction.addItem(funcname)

        for heuristic in self.ASTAR_HEURISTICS:
            self.dock.selectAstarHeuristic.addItem(heuristic)

        self.dock.selectAstarEpsilon.setMinimum(0)
        self.dock.selectAstarEpsilon.setMinimum(1)
        self.dock.selectAstarEpsilon.valueChanged.connect(self.astarEpsilonChanged)

        self.dock.lineEditIds.setValidator(QRegExpValidator(QRegExp("[0-9,]+"), self.dock))
        self.dock.lineEditPcts.setValidator(QRegExpValidator(QRegExp("[0-9,.]+"), self.dock))

        self.dock.lineEditSourceId.setValidator(QIntValidator())
        self.dock.lineEditTargetId.setValidator(QIntValidator())

        self.dock.lineEditSourcePos.setValidator(QDoubleValidator(0.0, 1.0, 10, self.dock))
        self.dock.lineEditTargetPos.setValidator(QDoubleValidator(0.0, 1.0, 10, self.dock))

        self.dock.lineEditTargetIds.setValidator(QRegExpValidator(QRegExp("[0-9,]+"), self.dock))
        self.dock.lineEditSourceIds.setValidator(QRegExpValidator(QRegExp("[0-9,]+"), self.dock))

        self.dock.lineEditDistance.setValidator(QDoubleValidator())
        self.dock.lineEditAlpha.setValidator(QDoubleValidator())
        self.dock.lineEditPaths.setValidator(QIntValidator())

        # populate the combo with connections
        self.reloadMessage = False
        self.reloadConnections()
        self.loadSettings()
        Utils.logMessage("startup version " + str(self.version))
        self.reloadMessage = True

    def show(self):
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dock)

    def unload(self):
        ''' Removes the plugin menu item and icon'''
        self.clear()
        self.saveSettings()
        # Remove the plugin menu item and icon
        self.iface.removePluginDatabaseMenu("&pgRouting Layer", self.action)
        self.iface.removeDockWidget(self.dock)

    def reloadConnections(self):
        ''' Reloads the connection with database. '''
        oldReloadMessage = self.reloadMessage
        self.reloadMessage = False
        database = str(self.dock.comboConnections.currentText())

        self.dock.comboConnections.clear()

        actions = conn.getAvailableConnections()
        self.actionsDb = {}
        for a in actions:
            self.actionsDb[str(a.text())] = a

        for dbname in self.actionsDb:
            db = None
            try:
                db = self.actionsDb[dbname].connect()
                con = db.con
                if (Utils.getPgrVersion(con) != 0):
                    self.dock.comboConnections.addItem(dbname)

            except dbConnection.DbError as e:
                Utils.logMessage("dbname:" + dbname + ", " + e.msg)

            finally:
                if db and db.con:
                    db.con.close()

        idx = self.dock.comboConnections.findText(database)

        if idx >= 0:
            self.dock.comboConnections.setCurrentIndex(idx)
        else:
            self.dock.comboConnections.setCurrentIndex(0)

        self.reloadMessage = oldReloadMessage
        self.updateConnectionEnabled()

    def updateConnectionEnabled(self):
        ''' Updates the database connection name and function '''
        dbname = str(self.dock.comboConnections.currentText())
        if dbname == '':
            return

        db = self.actionsDb[dbname].connect()
        con = db.con
        self.version = Utils.getPgrVersion(con)
        if self.reloadMessage:
            QMessageBox.information(self.dock, self.dock.windowTitle(),
                                    'Selected database: ' + dbname + '\npgRouting version: ' + str(self.version))

        currentFunction = str(self.dock.comboBoxFunction.currentText())
        if currentFunction == ' ':
            return

        self.loadFunctionsForVersion()
        self.updateFunctionEnabled(currentFunction)

    def loadFunctionsForVersion(self):
        ''' Loads function names based on pgr version. '''
        currentText = str(self.dock.comboBoxFunction.currentText())
        self.dock.comboBoxFunction.clear()

        # for funcname, function in self.functions.items():
        for funcname in self.functions:
            function = self.functions[funcname]
            if (function.isSupportedVersion(self.version)):
                self.dock.comboBoxFunction.addItem(function.getName())

        idx = self.dock.comboBoxFunction.findText(currentText)
        if idx >= 0:
            self.dock.comboBoxFunction.setCurrentIndex(idx)

    def updateFunctionEnabled(self, text):
        ''' Updates the GUI fields of the selected function. '''
        text = str(self.dock.comboBoxFunction.currentText())
        if text == '':
            return
        self.clear()
        function = self.functions.get(str(text))

        self.toggleSelectButton(None)

        for controlName in self.TOGGLE_CONTROL_NAMES:
            control = getattr(self.dock, controlName)
            control.setVisible(False)

        for controlName in function.getControlNames(self.version):
            control = getattr(self.dock, controlName)
            control.setVisible(True)

        # for initial display
        self.dock.gridLayoutSqlColumns.invalidate()
        self.dock.gridLayoutArguments.invalidate()

        if (not self.dock.checkBoxHasReverseCost.isChecked()) or (not self.dock.checkBoxHasReverseCost.isEnabled()):
            self.dock.lineEditReverseCost.setEnabled(False)

        # if type(edge/node) changed, clear input
        if (self.prevType is not None) and (self.prevType != function.isEdgeBase()):
            self.clear()

        self.prevType = function.isEdgeBase()

        canExport = function.canExport()
        self.dock.buttonExport.setEnabled(canExport)
        canExportMerged = function.canExportMerged()
        self.dock.buttonExportMerged.setEnabled(canExportMerged)

    def selectIds(self, checked):
        ''' Selects the ids and dispaly on lineEdit. '''
        if checked:
            self.toggleSelectButton(self.dock.buttonSelectIds)
            self.dock.lineEditIds.setText("")
            self.dock.lineEditPcts.setText("")
            if len(self.idsVertexMarkers) > 0:
                for marker in self.idsVertexMarkers:
                    marker.setVisible(False)
                self.idsVertexMarkers = []
            if len(self.idsRubberBands) > 0:
                for rubberBand in self.idsRubberBands:
                    rubberBand.reset(Utils.getRubberBandType(False))
                self.idsRubberBands = []
            self.iface.mapCanvas().setMapTool(self.idsEmitPoint)
        else:
            self.iface.mapCanvas().unsetMapTool(self.idsEmitPoint)

    def setIds(self, pt):
        ''' Sets the ids on mapCanvas with color '''
        function = self.functions[str(self.dock.comboBoxFunction.currentText())]
        args = self.getArguments()
        mapCanvas = self.iface.mapCanvas()
        if not function.isEdgeBase():
            result, the_id, wkt = self.findNearestNode(args, pt)
            if result:
                ids = self.dock.lineEditIds.text()
                if not ids:
                    self.dock.lineEditIds.setText(str(the_id))
                else:
                    self.dock.lineEditIds.setText(ids + "," + str(the_id))
                geom = QgsGeometry().fromWkt(wkt)
                vertexMarker = QgsVertexMarker(mapCanvas)
                vertexMarker.setColor(Qt.green)
                vertexMarker.setPenWidth(2)
                vertexMarker.setCenter(geom.asPoint())
                self.idsVertexMarkers.append(vertexMarker)
        else:
            result, the_id, wkt, pos, pointWkt = self.findNearestLink(args, pt)
            if result:
                ids = self.dock.lineEditIds.text()
                if not ids:
                    self.dock.lineEditIds.setText(str(the_id))
                else:
                    self.dock.lineEditIds.setText(ids + "," + str(the_id))
                geom = QgsGeometry().fromWkt(wkt)
                idRubberBand = QgsRubberBand(mapCanvas, Utils.getRubberBandType(False))
                idRubberBand.setColor(Qt.yellow)
                idRubberBand.setWidth(4)
                if geom.wkbType() == QgsWkbTypes.MultiLineString:
                    for line in geom.asMultiPolyline():
                        for pt in line:
                            idRubberBand.addPoint(pt)
                elif geom.wkbType() == QgsWkbTypes.LineString:
                    for pt in geom.asPolyline():
                        idRubberBand.addPoint(pt)
                self.idsRubberBands.append(idRubberBand)
                pcts = self.dock.lineEditPcts.text()
                if not pcts:
                    self.dock.lineEditPcts.setText(str(pos))
                else:
                    self.dock.lineEditPcts.setText(pcts + "," + str(pos))
                pointGeom = QgsGeometry().fromWkt(pointWkt)
                vertexMarker = QgsVertexMarker(mapCanvas)
                vertexMarker.setColor(Qt.green)
                vertexMarker.setPenWidth(2)
                vertexMarker.setCenter(pointGeom.asPoint())
                self.idsVertexMarkers.append(vertexMarker)
        Utils.refreshMapCanvas(mapCanvas)

    def selectSourceId(self, checked):
        ''' Selects the source id and dispaly its value on lineEdit. '''
        if checked:
            self.toggleSelectButton(self.dock.buttonSelectSourceId)
            self.dock.lineEditSourceId.setText("")
            self.sourceIdVertexMarker.setVisible(False)
            self.sourceIdRubberBand.reset(Utils.getRubberBandType(False))
            self.iface.mapCanvas().setMapTool(self.sourceIdEmitPoint)
        else:
            self.iface.mapCanvas().unsetMapTool(self.sourceIdEmitPoint)

    def setSourceId(self, pt):
        ''' Sets the source id by finding nearest node and displays in mapCanvas with color '''
        function = self.functions[str(self.dock.comboBoxFunction.currentText())]
        args = self.getArguments()
        if not function.isEdgeBase():
            result, source_id, wkt = self.findNearestNode(args, pt)
            if result:
                self.dock.lineEditSourceId.setText(str(source_id))
                geom = QgsGeometry().fromWkt(wkt)
                self.sourceIdVertexMarker.setCenter(geom.asPoint())
                self.sourceIdVertexMarker.setVisible(True)
                self.dock.buttonSelectSourceId.click()
        else:
            result, source_id, wkt, pos, pointWkt = self.findNearestLink(args, pt)
            if result:
                self.dock.lineEditSourceId.setText(str(source_id))
                geom = QgsGeometry().fromWkt(wkt)
                if geom.wkbType() == QgsWkbTypes.MultiLineString:
                    for line in geom.asMultiPolyline():
                        for pt in line:
                            self.sourceIdRubberBand.addPoint(pt)
                elif geom.wkbType() == QgsWkbTypes.LineString:
                    for pt in geom.asPolyline():
                        self.sourceIdRubberBand.addPoint(pt)
                self.dock.lineEditSourcePos.setText(str(pos))
                pointGeom = QgsGeometry().fromWkt(pointWkt)
                self.sourceIdVertexMarker.setCenter(pointGeom.asPoint())
                self.sourceIdVertexMarker.setVisible(True)
                self.dock.buttonSelectSourceId.click()
        Utils.refreshMapCanvas(self.iface.mapCanvas())

    def selectSourceIds(self, checked):
        ''' Selects the source ids and dispaly its value on lineEdit. '''
        if checked:
            self.toggleSelectButton(self.dock.buttonSelectSourceIds)
            self.dock.lineEditSourceIds.setText("")
            if len(self.sourceIdsVertexMarkers) > 0:
                for marker in self.sourceIdsVertexMarkers:
                    marker.setVisible(False)
                self.sourceIdsVertexMarkers = []
            self.iface.mapCanvas().setMapTool(self.sourceIdsEmitPoint)
        else:
            self.iface.mapCanvas().unsetMapTool(self.sourceIdsEmitPoint)

    def setSourceIds(self, pt):
        ''' Sets the source id by finding nearest node and displays in mapCanvas with color '''
        args = self.getArguments()
        result, source_id, wkt = self.findNearestNode(args, pt)
        if result:
            ids = self.dock.lineEditSourceIds.text()
            if not ids:
                self.dock.lineEditSourceIds.setText(str(source_id))
            else:
                self.dock.lineEditSourceIds.setText(ids + "," + str(source_id))
            geom = QgsGeometry().fromWkt(wkt)
            mapCanvas = self.iface.mapCanvas()
            vertexMarker = QgsVertexMarker(mapCanvas)
            vertexMarker.setColor(Qt.blue)
            vertexMarker.setPenWidth(2)
            vertexMarker.setCenter(geom.asPoint())
            self.sourceIdsVertexMarkers.append(vertexMarker)
            Utils.refreshMapCanvas(mapCanvas)

    def selectTargetId(self, checked):
        ''' Selects the target id and dispaly its value on lineEdit. '''
        if checked:
            self.toggleSelectButton(self.dock.buttonSelectTargetId)
            self.dock.lineEditTargetId.setText("")
            self.targetIdVertexMarker.setVisible(False)
            self.targetIdRubberBand.reset(Utils.getRubberBandType(False))
            self.iface.mapCanvas().setMapTool(self.targetIdEmitPoint)
        else:
            self.iface.mapCanvas().unsetMapTool(self.targetIdEmitPoint)

    def setTargetId(self, pt):
        ''' Sets the target id by finding nearest node and displays in mapCanvas with color '''
        function = self.functions[str(self.dock.comboBoxFunction.currentText())]
        args = self.getArguments()
        if not function.isEdgeBase():
            result, target_id, wkt = self.findNearestNode(args, pt)
            if result:
                self.dock.lineEditTargetId.setText(str(target_id))
                geom = QgsGeometry().fromWkt(wkt)
                self.targetIdVertexMarker.setCenter(geom.asPoint())
                self.targetIdVertexMarker.setVisible(True)
                self.dock.buttonSelectTargetId.click()
        else:
            result, target_id, wkt, pos, pointWkt = self.findNearestLink(args, pt)
            if result:
                self.dock.lineEditTargetId.setText(str(target_id))
                geom = QgsGeometry().fromWkt(wkt)
                if geom.wkbType() == QgsWkbTypes.MultiLineString:
                    for line in geom.asMultiPolyline():
                        for pt in line:
                            self.targetIdRubberBand.addPoint(pt)
                elif geom.wkbType() == QgsWkbTypes.LineString:
                    for pt in geom.asPolyline():
                        self.targetIdRubberBand.addPoint(pt)
                self.dock.lineEditTargetPos.setText(str(pos))
                pointGeom = QgsGeometry().fromWkt(pointWkt)
                self.targetIdVertexMarker.setCenter(pointGeom.asPoint())
                self.targetIdVertexMarker.setVisible(True)
                self.dock.buttonSelectTargetId.click()
        Utils.refreshMapCanvas(self.iface.mapCanvas())

    def selectTargetIds(self, checked):
        ''' Selects the target ids and dispaly its value on lineEdit. '''
        if checked:
            self.toggleSelectButton(self.dock.buttonSelectTargetIds)
            self.dock.lineEditTargetIds.setText("")
            if len(self.targetIdsVertexMarkers) > 0:
                for marker in self.targetIdsVertexMarkers:
                    marker.setVisible(False)
                self.targetIdsVertexMarkers = []
            self.iface.mapCanvas().setMapTool(self.targetIdsEmitPoint)
        else:
            self.iface.mapCanvas().unsetMapTool(self.targetIdsEmitPoint)

    def setTargetIds(self, pt):
        ''' Sets the target ids by finding nearest node and displays in mapCanvas with color '''
        args = self.getArguments()
        result, targetId, wkt = self.findNearestNode(args, pt)
        if result:
            ids = self.dock.lineEditTargetIds.text()
            if not ids:
                self.dock.lineEditTargetIds.setText(str(targetId))
            else:
                self.dock.lineEditTargetIds.setText(ids + "," + str(targetId))
            geom = QgsGeometry().fromWkt(wkt)
            mapCanvas = self.iface.mapCanvas()
            vertexMarker = QgsVertexMarker(mapCanvas)
            vertexMarker.setColor(Qt.green)
            vertexMarker.setPenWidth(2)
            vertexMarker.setCenter(geom.asPoint())
            self.targetIdsVertexMarkers.append(vertexMarker)
            Utils.refreshMapCanvas(mapCanvas)

    def astarEpsilonChanged(self, state):
        '''
        This method will be called when the epsilon slider is dragged by the user.
        The value() of the slider ranges from 1-99
        '''
        size = self.dock.selectAstarEpsilon.value() / 100
        self.dock.showAstarEpsilon.setText(str(size))

    def updateReverseCostEnabled(self, state):
        ''' Updates the reverse cost checkBox '''
        if state == Qt.Checked:
            self.dock.lineEditReverseCost.setEnabled(True)
        else:
            self.dock.lineEditReverseCost.setEnabled(False)

    def run(self):
        """ Draws a Preview on the canvas"""
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        db = None
        try:
            dbname = str(self.dock.comboConnections.currentText())
            db = self.actionsDb[dbname].connect()
            con = db.con

            function = self.functions[str(self.dock.comboBoxFunction.currentText())]
            args = self.getArguments()

            empties = []
            for key in list(args.keys()):
                if key != 'srid' and not args[key]:
                    empties.append(key)

            if len(empties) > 0:
                QApplication.restoreOverrideCursor()
                QMessageBox.warning(self.dock, self.dock.windowTitle(),
                                    'Following argument is not specified.\n' + ','.join(empties))
                return

            version = Utils.getPgrVersion(con)
            args['version'] = version

            if (function.getName() == 'tsp(euclid)'):
                args['node_query'] = PgrQ.getNodeQuery(args)

            function.prepare(self.canvasItemList)
            cur = con.cursor()
            cur.execute(function.getQuery(args).as_string(con))

            # QMessageBox.information(self.dock, self.dock.windowTitle(), 'Geometry Query:' +
            #        function.getQuery(args).as_string(con))

            rows = cur.fetchall()
            if len(rows) == 0:
                QMessageBox.information(self.dock, self.dock.windowTitle(),
                                        'No paths found in ' + self.getLayerName(args, con))

            args['canvas_srid'] = Utils.getCanvasSrid(Utils.getDestinationCrs(self.iface.mapCanvas()))
            Utils.setTransformQuotes(args, args['srid'], args['canvas_srid'])
            function.draw(rows, con, args, args['geomType'], self.canvasItemList, self.iface.mapCanvas())

        except psycopg2.DatabaseError as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)

        except SystemError as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)

        except AssertionError as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self.dock, self.dock.windowTitle(), '%s' % e)

        finally:
            QApplication.restoreOverrideCursor()
            if db and db.con:
                try:
                    db.con.close()
                except Exception:
                    QMessageBox.critical(self.dock, self.dock.windowTitle(),
                                         'server closed the connection unexpectedly')

    def export(self):
        ''' Exports the result layer '''
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        db = None
        try:
            dbname = str(self.dock.comboConnections.currentText())
            db = self.actionsDb[dbname].connect()
            con = db.con

            function = self.functions[str(self.dock.comboBoxFunction.currentText())]
            args = self.getArguments()

            empties = []
            for key in list(args.keys()):
                if key != 'srid' and not args[key]:
                    empties.append(key)

            if len(empties) > 0:
                QApplication.restoreOverrideCursor()
                QMessageBox.warning(self.dock, self.dock.windowTitle(),
                                    'Following argument is not specified.\n' + ','.join(empties))
                return

            version = Utils.getPgrVersion(con)

            args['version'] = version
            if (self.version != version):
                QMessageBox.warning(self.dock, self.dock.windowTitle(),
                                    'versions are different')

            # get the EXPORT query
            msgQuery = function.getExportQuery(args)
            # Utils.logMessage('Export:\n' + msgQuery.as_string(con))

            query = self.cleanQuery(msgQuery.as_string(con))

            uri = db.getURI()
            uri.setDataSource("", "(" + query + ")", "path_geom", "", "seq")

            layerName = self.getLayerName(args, con)

            vl = self.iface.addVectorLayer(uri.uri(), layerName, db.getProviderName())
            if not vl:
                QMessageBox.information(self.dock, self.dock.windowTitle(),
                                        'Invalid Layer:\n - No paths found or\n - Failed to create vector layer from query')

        except psycopg2.DatabaseError as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)

        except SystemError as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)

        finally:
            QApplication.restoreOverrideCursor()
            if db and db.con:
                try:
                    db.con.close()
                except Exception:
                    QMessageBox.critical(self.dock, self.dock.windowTitle(),
                                         'server closed the connection unexpectedly')

    @classmethod
    def cleanQuery(cls, msgQuery):
        ''' Cleans the query '''
        query = msgQuery.replace('\n', ' ')
        query = re.sub(r'\s+', ' ', query)
        query = query.replace('( ', '(')
        query = query.replace(' )', ')')
        query = query.strip()
        return query

    def getBBOX(self, srid):
        """
        Returns the in ready to use args: BBOX , printBBOX
        """
        bbox = {}
        canvasCrs = Utils.getDestinationCrs(self.iface.mapCanvas())
        canvasSrid = Utils.getCanvasSrid(canvasCrs)
        bbox['srid'] = sql.Literal(canvasSrid)
        bbox['prefix'] = sql.SQL("")
        bbox['suffix'] = sql.SQL("")
        if srid != canvasSrid:
            if srid == 0:
                bbox['prefix'] = sql.SQL("ST_SetSRID(")
            else:
                bbox['prefix'] = sql.SQL("ST_Transform(")
            bbox['suffix'] = sql.SQL(", {})").format(sql.Literal(srid))
        xMin = self.iface.mapCanvas().extent().xMinimum()
        yMin = self.iface.mapCanvas().extent().yMinimum()
        xMax = self.iface.mapCanvas().extent().xMaximum()
        yMax = self.iface.mapCanvas().extent().yMaximum()
        bbox['xMin'] = sql.Literal(xMin)
        bbox['yMin'] = sql.Literal(yMin)
        bbox['xMax'] = sql.Literal(xMax)
        bbox['yMax'] = sql.Literal(yMax)
        text = "BBOX(" + str(round(xMin, 2))
        text += " " + str(round(yMin, 2))
        text += "," + str(round(xMax, 2))
        text += " " + str(round(yMax, 2)) + ")"
        return sql.SQL("""
           ST_MakeEnvelope(
              {xMin}, {yMin},
              {xMax}, {yMax}, {srid}
              )
        """).format(**bbox), text

    def exportMerged(self):
        ''' exports the result layer with input layer '''
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        db = None
        try:
            dbname = str(self.dock.comboConnections.currentText())
            db = self.actionsDb[dbname].connect()
            con = db.con

            function = self.functions[str(self.dock.comboBoxFunction.currentText())]
            args = self.getArguments()

            empties = []
            for key in list(args.keys()):
                if key != 'srid' and not args[key]:
                    empties.append(key)

            if len(empties) > 0:
                QApplication.restoreOverrideCursor()
                QMessageBox.warning(self.dock, self.dock.windowTitle(),
                                    'Following argument is not specified.\n' + ','.join(empties))
                return

            version = Utils.getPgrVersion(con)
            args['version'] = version

            # get the exportMerge query
            msgQuery = function.getExportMergeQuery(args)
            Utils.logMessage('Export merged:\n' + msgQuery.as_string(con))

            query = self.cleanQuery(msgQuery.as_string(con))

            uri = db.getURI()
            uri.setDataSource("", "(" + query + ")", "path_geom", "", "seq")

            # add vector layer to map
            layerName = self.getLayerName(args, con, 'M')

            vl = self.iface.addVectorLayer(uri.uri(), layerName, db.getProviderName())
            if not vl:

                bigIntFunctions = [
                    'dijkstra',
                    'drivingDistance',
                    'ksp',
                    'alphaShape'
                ]
                if function.getName() in bigIntFunctions:
                    QMessageBox.information(self.dock, self.dock.windowTitle(),
                                            'Invalid Layer:\n - No paths found')
                else:
                    QMessageBox.information(self.dock, self.dock.windowTitle(),
                                            'Invalid Layer:\n - No paths found or\n - Failed to create vector layer from query')

        except psycopg2.DatabaseError as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)

        except SystemError as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)

        finally:
            QApplication.restoreOverrideCursor()
            if db and db.con:
                try:
                    db.con.close()
                except Exception:
                    QMessageBox.critical(self.dock, self.dock.windowTitle(),
                                         'server closed the connection unexpectedly')

    def getLayerName(self, args, con, letter=''):
        ''' returns the layer Name '''
        function = self.functions[str(self.dock.comboBoxFunction.currentText())]

        layerName = "(" + letter

        if 'directed' in args and args['directed'] == 'true':
            layerName += "D) "
        else:
            layerName += "U) "

        layerName += function.getName() + ": "

        if 'source_id' in args:
            layerName += args['source_id'].as_string(con)
        elif 'ids' in args:
            layerName += "{" + args['ids'] + "}"
        else:
            layerName += "[" + args['source_ids'].as_string(con) + "]"

        if 'ids' in args:
            layerName += " "
        elif 'distance' in args:
            layerName += " dd = " + args['distance']
        else:
            layerName += " to "
            if 'target_id' in args:
                layerName += args['target_id'].as_string(con)
            else:
                layerName += "[" + args['target_ids'].as_string(con) + "]"

        if 'paths' in args:
            layerName += " -  K = " + args['paths']
            if 'heap_paths' in args and args['heap_paths'] == 'true':
                layerName += '+'
        layerName += " " + args['printBBOX']

        return layerName

    def clear(self):
        ''' Clears the selected ids '''
        # self.dock.lineEditIds.setText("")
        for marker in self.idsVertexMarkers:
            marker.setVisible(False)
        self.idsVertexMarkers = []

        # self.dock.lineEditSourceIds.setText("")
        for marker in self.sourceIdsVertexMarkers:
            marker.setVisible(False)
        self.sourceIdsVertexMarkers = []

        # self.dock.lineEditTargetIds.setText("")
        for marker in self.targetIdsVertexMarkers:
            marker.setVisible(False)
        self.targetIdsVertexMarkers = []

        # self.dock.lineEditPcts.setText("")
        # self.dock.lineEditSourceId.setText("")
        self.sourceIdVertexMarker.setVisible(False)
        # self.dock.lineEditSourcePos.setText("0.5")
        # self.dock.lineEditTargetId.setText("")
        self.targetIdVertexMarker.setVisible(False)
        # self.dock.lineEditTargetPos.setText("0.5")
        for rubberBand in self.idsRubberBands:
            rubberBand.reset(Utils.getRubberBandType(False))
        self.idsRubberBands = []
        self.sourceIdRubberBand.reset(Utils.getRubberBandType(False))
        self.targetIdRubberBand.reset(Utils.getRubberBandType(False))
        for marker in self.canvasItemList['markers']:
            marker.setVisible(False)
        self.canvasItemList['markers'] = []
        for anno in self.canvasItemList['annotations']:
            try:
                anno.setVisible(False)
            except RuntimeError as e:
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)
        self.canvasItemList['annotations'] = []
        for path in self.canvasItemList['paths']:
            path.reset(Utils.getRubberBandType(False))
        self.canvasItemList['paths'] = []
        self.canvasItemList['path'].reset(Utils.getRubberBandType(False))
        self.canvasItemList['area'].reset(Utils.getRubberBandType(True))

    def toggleSelectButton(self, button):
        selectButtons = [
            self.dock.buttonSelectIds,
            self.dock.buttonSelectSourceId,
            self.dock.buttonSelectTargetId
        ]
        for selectButton in selectButtons:
            if selectButton != button:
                if selectButton.isChecked():
                    selectButton.click()

    def get_innerQueryArguments(self, controls):
        args = {}

        args['edge_schema'] = sql.Identifier(str(self.dock.lineEditSchema.text()))
        args['edge_table'] = sql.Identifier(str(self.dock.lineEditTable.text()))
        args['geometry'] = sql.Identifier(str(self.dock.lineEditGeometry.text()))
        args['id'] = sql.Identifier(str(self.dock.lineEditId.text()))
        args['source'] = sql.Identifier(str(self.dock.lineEditSource.text()))
        args['target'] = sql.Identifier(str(self.dock.lineEditTarget.text()))
        args['cost'] = sql.Identifier(str(self.dock.lineEditCost.text()))

        if not self.dock.checkBoxHasReverseCost.isChecked():
            args['reverse_cost'] = sql.SQL(" -1 ")
        else:
            args['reverse_cost'] = sql.SQL("{}").format(sql.Identifier(
                                                        str(self.dock.lineEditReverseCost.text())))

        if 'lineEditX1' in controls:
            args['x1'] = sql.Identifier(self.dock.lineEditX1.text())
            args['y1'] = sql.Identifier(self.dock.lineEditY1.text())
            args['x2'] = sql.Identifier(self.dock.lineEditX2.text())
            args['y2'] = sql.Identifier(self.dock.lineEditY2.text())

        return args

    def get_whereClause(self, edge_schema, edge_table, geometry, conn):
        args = {}
        args['srid'], args['geomType'] = Utils.getSridAndGeomType(conn, edge_schema, edge_table, geometry)
        args['dbsrid'] = sql.Literal(args['srid'])
        if self.dock.checkBoxUseBBOX.isChecked():
            args['BBOX'], args['printBBOX'] = self.getBBOX(args['srid'])
            args['where_clause'] = sql.SQL(' WHERE {0}.{1} && {2}').format(edge_table, geometry,
                                                                           args['BBOX'])
        else:
            args['BBOX'] = sql.SQL("")
            args['printBBOX'] = ' '
            args['where_clause'] = sql.SQL(' WHERE true ')

        return args

    def get_innerQuery(self, controls, conn):
        args = {}
        args = self.get_innerQueryArguments(controls)
        args.update(self.get_whereClause(args['edge_schema'], args['edge_table'], args['geometry'], conn))

        if 'lineEditX1' not in controls:
            args['innerQuery'] = PgrQ.getEdgesQuery(args)
        else:
            args['innerQuery'] = PgrQ.getEdgesQueryXY(args)

        return args

    def getArguments(self):
        ''' updates the GUI field text to args '''
        db = None
        try:
            dbname = str(self.dock.comboConnections.currentText())
            db = self.actionsDb[dbname].connect()

            function = self.functions[str(self.dock.comboBoxFunction.currentText())]
            return self._getArguments(function.getControlNames(self.version), db.con)

        except psycopg2.DatabaseError as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)

        except SystemError as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)

        except AssertionError as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self.dock, self.dock.windowTitle(), '%s' % e)

        finally:
            QApplication.restoreOverrideCursor()
            if db and db.con:
                try:
                    db.con.close()
                except Exception:
                    QMessageBox.critical(self.dock, self.dock.windowTitle(),
                                         'server closed the connection unexpectedly')

    def _getArguments(self, controls, conn):
        ''' updates the GUI field text to args '''

        args = {}
        args = self.get_innerQuery(controls, conn)
        function = str(self.dock.comboBoxFunction.currentText()).lower()
        args['function'] = sql.Identifier(str(function))

        if function in ['pgr_astarcost', 'pgr_dijkstracost', 'pgr_bdastarcost', 'pgr_bddijkstracost']:
            # TODO: capture vertices table, geometry of vertices table
            args['vertex_schema'] = sql.Identifier(str(self.dock.lineEditSchema.text()))
            args['vertex_table'] = sql.Identifier(str(self.dock.lineEditTable.text()) + '_vertices_pgr')
            args['geometry_vt'] = sql.Identifier(str(self.dock.lineEditGeometry.text()))
            # QMessageBox.information(self.dock, self.dock.windowTitle(),
            #    'TODO: capture vertices table, geometry of vertices table, label the edges')

        if 'lineEditX1' in controls:
            args['astarHeuristic'] = sql.Literal(str(self.dock.selectAstarHeuristic.currentIndex()))
            args['astarFactor'] = sql.Literal(str(self.dock.selectAstarFactor.text()))
            args['astarEpsilon'] = sql.Literal(str(self.dock.selectAstarEpsilon.value()))

        # args['rule'] = self.dock.lineEditRule.text() if 'lineEditRule' in controls
        # args['to_cost'] = self.dock.lineEditToCost.text() if 'lineEditToCost' in controls:

        if 'lineEditIds' in controls:
            args['ids'] = self.dock.lineEditIds.text()

        if 'lineEditPcts' in controls:
            args['pcts'] = self.dock.lineEditPcts.text()

        # Used in pgr_KSP
        if 'lineEditSourceId' in controls:
            args['source_id'] = sql.Literal(self.dock.lineEditSourceId.text())
            args['target_id'] = sql.Literal(self.dock.lineEditTargetId.text())

        # Used in pgr_KSP
        if 'lineEditPaths' in controls:
            args['Kpaths'] = sql.Literal(self.dock.lineEditPaths.text())

        if 'lineEditSourcePos' in controls:
            args['source_pos'] = self.dock.lineEditSourcePos.text()

        if 'lineEditSourceIds' in controls:
            args['source_ids'] = sql.SQL("string_to_array({}, ',')::BIGINT[]").format(sql.Literal(str(self.dock.lineEditSourceIds.text())))

        if 'lineEditTargetPos' in controls:
            args['target_pos'] = self.dock.lineEditTargetPos.text()

        if 'lineEditTargetIds' in controls:
            args['target_ids'] = sql.SQL("string_to_array({}, ',')::BIGINT[]").format(sql.Literal(str(self.dock.lineEditTargetIds.text())))

        if 'lineEditDistance' in controls:
            args['distance'] = self.dock.lineEditDistance.text()

        if 'lineEditAlpha' in controls:
            args['alpha'] = self.dock.lineEditAlpha.text()

        args['directed'] = sql.SQL("directed := {}::BOOLEAN").format(sql.Literal(str(self.dock.checkBoxDirected.isChecked()).lower()))

        if 'checkBoxHeapPaths' in controls:
            args['heap_paths'] = sql.SQL("heap_paths := {}::BOOLEAN").format(sql.Literal(str(self.dock.checkBoxHeapPaths.isChecked()).lower()))

        # if 'labelDrivingSide' in controls:
        #     args['driving_side'] = str('b')
        #     if (self.dock.checkBoxLeft.isChecked() == True and self.dock.checkBoxRight.isChecked() == False):
        #         args['driving_side'] = str('l')
        #     elif (self.dock.checkBoxLeft.isChecked() == False and self.dock.checkBoxRight.isChecked() == True):
        #         args['driving_side'] = str('r')

        return args

    # emulate "matching.sql" - "find_nearest_node_within_distance"
    def findNearestNode(self, args, pt):
        ''' finds the nearest node to selected point '''
        distance = self.iface.mapCanvas().getCoordinateTransform().mapUnitsPerPixel() * self.FIND_RADIUS
        rect = QgsRectangle(pt.x() - distance, pt.y() - distance, pt.x() + distance, pt.y() + distance)
        canvasCrs = Utils.getDestinationCrs(self.iface.mapCanvas())
        layerCrs = QgsCoordinateReferenceSystem()
        Utils.createFromSrid(layerCrs, args['srid'])
        trans = QgsCoordinateTransform(canvasCrs, layerCrs, QgsProject.instance())
        pt = trans.transform(pt)
        rect = trans.transform(rect)

        args['canvas_srid'] = Utils.getCanvasSrid(canvasCrs)
        args['dbcanvas_srid'] = sql.Literal(args['canvas_srid'])
        args['x'] = sql.Literal(pt.x())
        args['y'] = sql.Literal(pt.y())
        args['SBBOX'] = self.getBBOX(args['srid'])[0]
        args['geom_t'] = Utils.getTransformedGeom(args['srid'], args['dbcanvas_srid'], args['geometry'])

        db, cur = self._exec_sql(PgrQ.get_closestVertexInfo(args))
        if cur:
            row = cur.fetchone()
            db.con.close()
            return True, row[0], row[2]
        else:
            return False, None, None

    # emulate "matching.sql" - "find_nearest_link_within_distance"
    def findNearestLink(self, args, pt):
        ''' finds the nearest link to selected point '''
        distance = self.iface.mapCanvas().getCoordinateTransform().mapUnitsPerPixel() * self.FIND_RADIUS
        rect = QgsRectangle(pt.x() - distance, pt.y() - distance, pt.x() + distance, pt.y() + distance)
        canvasCrs = Utils.getDestinationCrs(self.iface.mapCanvas())

        layerCrs = QgsCoordinateReferenceSystem()
        Utils.createFromSrid(layerCrs, args['srid'])
        trans = QgsCoordinateTransform(canvasCrs, layerCrs, QgsProject.instance())
        pt = trans.transform(pt)
        rect = trans.transform(rect)

        args['canvas_srid'] = Utils.getCanvasSrid(canvasCrs)
        args['x'] = pt.x()
        args['y'] = pt.y()
        args['minx'] = rect.xMinimum()
        args['miny'] = rect.yMinimum()
        args['maxx'] = rect.xMaximum()
        args['maxy'] = rect.yMaximum()
        args['decimal_places'] = self.FRACTION_DECIMAL_PLACES

        Utils.setTransformQuotes(args, args['srid'], args['canvas_srid'])

        db, cur = self._exec_sql(PgrQ.get_closestEdgeInfo(args))
        if cur:
            row = cur.fetchone()
            db.con.close()
            return True, row[0], row[2], row[3], [4]
        else:
            return False, None, None, None, None

    def loadSettings(self):
        ''' loads the  default settings '''
        settings = QSettings()
        idx = self.dock.comboConnections.findText(Utils.getStringValue(settings, '/pgRoutingLayer/Database', ''))
        if idx >= 0:
            self.dock.comboConnections.setCurrentIndex(idx)
        idx = self.dock.comboBoxFunction.findText(Utils.getStringValue(settings, '/pgRoutingLayer/Function', 'dijkstra'))
        if idx >= 0:
            self.dock.comboBoxFunction.setCurrentIndex(idx)

        self.dock.lineEditSchema.setText(Utils.getStringValue(settings, '/pgRoutingLayer/sql/edge_schema', 'edge_schema'))
        self.dock.lineEditTable.setText(Utils.getStringValue(settings, '/pgRoutingLayer/sql/edge_table', 'edge_table'))
        self.dock.lineEditGeometry.setText(Utils.getStringValue(settings, '/pgRoutingLayer/sql/geometry', 'the_geom'))

        self.dock.lineEditId.setText(Utils.getStringValue(settings, '/pgRoutingLayer/sql/id', 'id'))
        self.dock.lineEditSource.setText(Utils.getStringValue(settings, '/pgRoutingLayer/sql/source', 'source'))
        self.dock.lineEditTarget.setText(Utils.getStringValue(settings, '/pgRoutingLayer/sql/target', 'target'))
        self.dock.lineEditCost.setText(Utils.getStringValue(settings, '/pgRoutingLayer/sql/cost', 'cost'))
        self.dock.lineEditReverseCost.setText(Utils.getStringValue(settings, '/pgRoutingLayer/sql/reverse_cost', 'reverse_cost'))

        self.dock.lineEditX1.setText(Utils.getStringValue(settings, '/pgRoutingLayer/sql/x1', 'x1'))
        self.dock.lineEditY1.setText(Utils.getStringValue(settings, '/pgRoutingLayer/sql/y1', 'y1'))
        self.dock.lineEditX2.setText(Utils.getStringValue(settings, '/pgRoutingLayer/sql/x2', 'x2'))
        self.dock.lineEditY2.setText(Utils.getStringValue(settings, '/pgRoutingLayer/sql/y2', 'y2'))

        self.dock.selectAstarHeuristic.setCurrentIndex(int(Utils.getStringValue(settings, '/pgRoutingLayer/sql/heuristic', '5')))
        self.dock.selectAstarFactor.setText(Utils.getStringValue(settings, '/pgRoutingLayer/sql/factor', '1'))
        self.dock.selectAstarEpsilon.setTickPosition(int(Utils.getStringValue(settings, '/pgRoutingLayer/sql/epsilon', '100')))

        # self.dock.lineEditRule.setText(Utils.getStringValue(settings, '/pgRoutingLayer/sql/rule', 'rule'))
        # self.dock.lineEditToCost.setText(Utils.getStringValue(settings, '/pgRoutingLayer/sql/to_cost', 'to_cost'))

        self.dock.lineEditIds.setText(Utils.getStringValue(settings, '/pgRoutingLayer/ids', ''))
        self.dock.lineEditPcts.setText(Utils.getStringValue(settings, '/pgRoutingLayer/pcts', ''))

        self.dock.lineEditSourceId.setText(Utils.getStringValue(settings, '/pgRoutingLayer/source_id', ''))
        self.dock.lineEditSourceIds.setText(Utils.getStringValue(settings, '/pgRoutingLayer/source_ids', ''))

        self.dock.lineEditTargetId.setText(Utils.getStringValue(settings, '/pgRoutingLayer/target_id', ''))
        self.dock.lineEditTargetIds.setText(Utils.getStringValue(settings, '/pgRoutingLayer/target_ids', ''))

        self.dock.lineEditSourcePos.setText(Utils.getStringValue(settings, '/pgRoutingLayer/source_pos', '0.5'))
        self.dock.lineEditTargetPos.setText(Utils.getStringValue(settings, '/pgRoutingLayer/target_pos', '0.5'))

        self.dock.lineEditDistance.setText(Utils.getStringValue(settings, '/pgRoutingLayer/distance', ''))
        self.dock.lineEditAlpha.setText(Utils.getStringValue(settings, '/pgRoutingLayer/alpha', '0.0'))
        self.dock.lineEditPaths.setText(Utils.getStringValue(settings, '/pgRoutingLayer/paths', '2'))
        self.dock.checkBoxDirected.setChecked(Utils.getBoolValue(settings, '/pgRoutingLayer/directed', False))
        self.dock.checkBoxHeapPaths.setChecked(Utils.getBoolValue(settings, '/pgRoutingLayer/heap_paths', False))
        self.dock.checkBoxHasReverseCost.setChecked(Utils.getBoolValue(settings, '/pgRoutingLayer/has_reverse_cost', False))

    def saveSettings(self):
        settings = QSettings()
        settings.setValue('/pgRoutingLayer/Database', self.dock.comboConnections.currentText())
        settings.setValue('/pgRoutingLayer/Function', self.dock.comboBoxFunction.currentText())

        settings.setValue('/pgRoutingLayer/sql/edge_schema', self.dock.lineEditSchema.text())
        settings.setValue('/pgRoutingLayer/sql/edge_table', self.dock.lineEditTable.text())
        # settings.setValue('/pgRoutingLayer/sql/pointsOfInterest', self.dock.lineEditPointsTable.text())
        settings.setValue('/pgRoutingLayer/sql/geometry', self.dock.lineEditGeometry.text())

        settings.setValue('/pgRoutingLayer/sql/id', self.dock.lineEditId.text())
        settings.setValue('/pgRoutingLayer/sql/source', self.dock.lineEditSource.text())
        settings.setValue('/pgRoutingLayer/sql/target', self.dock.lineEditTarget.text())
        settings.setValue('/pgRoutingLayer/sql/cost', self.dock.lineEditCost.text())
        settings.setValue('/pgRoutingLayer/sql/reverse_cost', self.dock.lineEditReverseCost.text())

        settings.setValue('/pgRoutingLayer/sql/x1', self.dock.lineEditX1.text())
        settings.setValue('/pgRoutingLayer/sql/y1', self.dock.lineEditY1.text())
        settings.setValue('/pgRoutingLayer/sql/x2', self.dock.lineEditX2.text())
        settings.setValue('/pgRoutingLayer/sql/y2', self.dock.lineEditY2.text())
        settings.setValue('/pgRoutingLayer/sql/heuristic', self.dock.selectAstarHeuristic.currentIndex())
        settings.setValue('/pgRoutingLayer/sql/factor', self.dock.selectAstarFactor.text())
        settings.setValue('/pgRoutingLayer/sql/epsilon', self.dock.selectAstarEpsilon.tickPosition())

        # settings.setValue('/pgRoutingLayer/sql/rule', self.dock.lineEditRule.text())
        # settings.setValue('/pgRoutingLayer/sql/to_cost', self.dock.lineEditToCost.text())

        settings.setValue('/pgRoutingLayer/ids', self.dock.lineEditIds.text())
        settings.setValue('/pgRoutingLayer/pcts', self.dock.lineEditPcts.text())
        settings.setValue('/pgRoutingLayer/source_pos', self.dock.lineEditSourcePos.text())
        settings.setValue('/pgRoutingLayer/target_pos', self.dock.lineEditTargetPos.text())

        settings.setValue('/pgRoutingLayer/source_id', self.dock.lineEditSourceId.text())
        settings.setValue('/pgRoutingLayer/target_id', self.dock.lineEditTargetId.text())

        settings.setValue('/pgRoutingLayer/source_ids', self.dock.lineEditSourceIds.text())
        settings.setValue('/pgRoutingLayer/target_ids', self.dock.lineEditTargetIds.text())

        settings.setValue('/pgRoutingLayer/distance', self.dock.lineEditDistance.text())
        settings.setValue('/pgRoutingLayer/alpha', self.dock.lineEditAlpha.text())
        settings.setValue('/pgRoutingLayer/paths', self.dock.lineEditPaths.text())
        settings.setValue('/pgRoutingLayer/directed', self.dock.checkBoxDirected.isChecked())
        settings.setValue('/pgRoutingLayer/heap_paths', self.dock.checkBoxHeapPaths.isChecked())
        settings.setValue('/pgRoutingLayer/has_reverse_cost', self.dock.checkBoxHasReverseCost.isChecked())

    def openHelp(self, checked):
        function = str(self.dock.comboBoxFunction.currentText())
        db = None
        try:
            dbname = str(self.dock.comboConnections.currentText())
            db = self.actionsDb[dbname].connect()
            con = db.con
            version = Utils.getPgrVersion(con)
        except psycopg2.DatabaseError:
            # database didn't have pgrouting
            return 0
        except SystemError:
            return 0
        url = QUrl('https://docs.pgrouting.org/' + str(version) + '/en/' + function + '.html')
        try:
            QDesktopServices.openUrl(url)
        except Exception:
            QMessageBox.information(self.dock, self.dock.windowTitle(),
                                    "Network error: No connection. \n Please check your network connection.")
            return

    # Caller must close the connection to the database
    def _exec_sql(self, query):
        db = None
        try:
            dbname = str(self.dock.comboConnections.currentText())
            db = self.actionsDb[dbname].connect()
            cursor = db.con.cursor()
            cursor.execute(query.as_string(db.con))
            return db, cursor

        except psycopg2.Error as e:
            # do the rollback to avoid a "current transaction aborted, commands ignored" errors
            db.con.rollback()
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)
            if db and db.con:
                db.con.close()
            return None, None
