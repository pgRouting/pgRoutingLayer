"""
/***************************************************************************
 pgRouting Layer
                                 a QGIS plugin
                                 
 based on "Fast SQL Layer" plugin. Copyright 2011 Pablo Torres Carreira 
                             -------------------
        begin                : 2011-11-25
        copyright            : (c) 2011 by Anita Graser
        email                : anita.graser.at@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
# Import the PyQt and QGIS libraries
from PyQt4 import uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import dbConnection
import pgRoutingLayer_utils as Utils
#import highlighter as hl
import os
import psycopg2
import re

conn = dbConnection.ConnectionManager()

class PgRoutingLayer:

    SUPPORTED_FUNCTIONS = [
        'dijkstra',
        'astar',
        #'shootingStar',
        'drivingDistance',
        'alphashape',
        'tsp_euclid',
        'trsp_vertex',
        'trsp_edge',
        'kdijkstra_cost',
        'kdijkstra_path',
        'bdDijkstra',
        'bdAstar',
        'ksp',
        'trsp_via_vertices',
        'trsp_via_edges'
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
        'labelRule', 'lineEditRule',
        'labelToCost', 'lineEditToCost',
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
        'checkBoxDirected', 'checkBoxHasReverseCost', 'checkBoxHeapPaths',
        'labelTurnRestrictSql', 'plainTextEditTurnRestrictSql',
    ]
    FIND_RADIUS = 10
    FRACTION_DECIMAL_PLACES = 2
    version = 2.0
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
        if not Utils.isQGISv1():
            resultAreaRubberBand.setBrushStyle(Qt.Dense4Pattern)
        self.canvasItemList['area'] = resultAreaRubberBand
        
    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(QIcon(":/plugins/pgRoutingLayer/icon.png"), "pgRouting Layer", self.iface.mainWindow())
        #Add toolbar button and menu item
        self.iface.addPluginToDatabaseMenu("&pgRouting Layer", self.action)
        #self.iface.addToolBarIcon(self.action)
        
        #load the form
        path = os.path.dirname(os.path.abspath(__file__))
        self.dock = uic.loadUi(os.path.join(path, "ui_pgRoutingLayer.ui"))
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
        
        self.idsEmitPoint = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.sourceIdEmitPoint = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.targetIdEmitPoint = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.sourceIdsEmitPoint = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.targetIdsEmitPoint = QgsMapToolEmitPoint(self.iface.mapCanvas())

        #self.idsEmitPoint.setButton(buttonSelectIds)
        #self.targetIdEmitPoint.setButton(buttonSelectTargetId)
        #self.sourceIdEmitPoint.setButton(buttonSelectSourceId)
        #self.targetIdsEmitPoint.setButton(buttonSelectTargetId)
        
        #connect the action to each method
        QObject.connect(self.action, SIGNAL("triggered()"), self.show)
        QObject.connect(self.dock.buttonReloadConnections, SIGNAL("clicked()"), self.reloadConnections)
        QObject.connect(self.dock.comboConnections, SIGNAL("currentIndexChanged(const QString&)"), self.updateConnectionEnabled)
        QObject.connect(self.dock.comboBoxFunction, SIGNAL("currentIndexChanged(const QString&)"), self.updateFunctionEnabled)

        QObject.connect(self.dock.buttonSelectIds, SIGNAL("clicked(bool)"), self.selectIds)
        QObject.connect(self.idsEmitPoint, SIGNAL("canvasClicked(const QgsPoint&, Qt::MouseButton)"), self.setIds)

        # One source id can be selected in some functions/version
        QObject.connect(self.dock.buttonSelectSourceId, SIGNAL("clicked(bool)"), self.selectSourceId)
        QObject.connect(self.sourceIdEmitPoint, SIGNAL("canvasClicked(const QgsPoint&, Qt::MouseButton)"), self.setSourceId)

        QObject.connect(self.dock.buttonSelectTargetId, SIGNAL("clicked(bool)"), self.selectTargetId)
        QObject.connect(self.targetIdEmitPoint, SIGNAL("canvasClicked(const QgsPoint&, Qt::MouseButton)"), self.setTargetId)

        # More than one source id can be selected in some functions/version
        QObject.connect(self.dock.buttonSelectSourceIds, SIGNAL("clicked(bool)"), self.selectSourceIds)
        QObject.connect(self.sourceIdsEmitPoint, SIGNAL("canvasClicked(const QgsPoint&, Qt::MouseButton)"), self.setSourceIds)

        QObject.connect(self.dock.buttonSelectTargetIds, SIGNAL("clicked(bool)"), self.selectTargetIds)
        QObject.connect(self.targetIdsEmitPoint, SIGNAL("canvasClicked(const QgsPoint&, Qt::MouseButton)"), self.setTargetIds)

        QObject.connect(self.dock.checkBoxHasReverseCost, SIGNAL("stateChanged(int)"), self.updateReverseCostEnabled)

        QObject.connect(self.dock.buttonRun, SIGNAL("clicked()"), self.run)
        QObject.connect(self.dock.buttonExport, SIGNAL("clicked()"), self.export)
        QObject.connect(self.dock.buttonExportMerged, SIGNAL("clicked()"), self.exportMerged)
        QObject.connect(self.dock.buttonClear, SIGNAL("clicked()"), self.clear)

        self.prevType = None
        self.functions = {}
        for funcfname in self.SUPPORTED_FUNCTIONS:
            # import the function
            exec("from functions import %s as function" % funcfname)
            funcname = function.Function.getName()
            self.functions[funcname] = function.Function(self.dock)
            self.dock.comboBoxFunction.addItem(funcname)
        
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
        self.loadSettings()
        
        #populate the combo with connections
        self.reloadMessage = False
        self.reloadConnections()
        Utils.logMessage("startup version " + str(self.version))
        self.reloadMessage = True
        
    def show(self):
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
        
    def unload(self):
        self.saveSettings()
        self.clear()
        # Remove the plugin menu item and icon
        self.iface.removePluginDatabaseMenu("&pgRouting Layer", self.action)
        self.iface.removeDockWidget(self.dock)
        
    def reloadConnections(self):
        oldReloadMessage = self.reloadMessage
        self.reloadMessage = False
        database = str(self.dock.comboConnections.currentText())

        self.dock.comboConnections.clear()

        actions = conn.getAvailableConnections()
        self.actionsDb = {}
        for a in actions:
            self.actionsDb[ unicode(a.text()) ] = a

        for dbname in self.actionsDb:
            db = None
            try:
                db = self.actionsDb[dbname].connect()
                con = db.con
                version = Utils.getPgrVersion(con)
                if (Utils.getPgrVersion(con) != 0):
                    self.dock.comboConnections.addItem(dbname)

            except dbConnection.DbError, e:
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
        dbname = str(self.dock.comboConnections.currentText())
        if dbname =='':
            return

        db = self.actionsDb[dbname].connect()
        con = db.con
        self.version = Utils.getPgrVersion(con)
        if self.reloadMessage:
            QMessageBox.information(self.dock, self.dock.windowTitle(), 
                'Selected database: ' + dbname + '\npgRouting version: ' + str(self.version))


        currentFunction = self.dock.comboBoxFunction.currentText()
        if currentFunction =='':
            return

        self.loadFunctionsForVersion()
        self.updateFunctionEnabled(currentFunction)

    def loadFunctionsForVersion(self):
        currentText = str(self.dock.comboBoxFunction.currentText())
        self.dock.comboBoxFunction.clear()

        #for funcname, function in self.functions.items():
        for funcname in sorted(self.functions):
            function = self.functions[funcname]
            if (function.isSupportedVersion(self.version)):
                self.dock.comboBoxFunction.addItem(function.getName())

        idx = self.dock.comboBoxFunction.findText(currentText)
        if idx >= 0:
            self.dock.comboBoxFunction.setCurrentIndex(idx)



    def updateFunctionEnabled(self, text):
        if text == '':
            return
        self.clear()
        function = self.functions[str(text)]
        
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
        if (self.prevType != None) and (self.prevType != function.isEdgeBase()):
            self.clear()
            
        self.prevType = function.isEdgeBase()

        canExport = function.canExport()
        self.dock.buttonExport.setEnabled(canExport)
        canExportMerged = function.canExportMerged()
        self.dock.buttonExportMerged.setEnabled(canExportMerged)
   
    def selectIds(self, checked):
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
        function = self.functions[str(self.dock.comboBoxFunction.currentText())]
        args = self.getBaseArguments()
        mapCanvas = self.iface.mapCanvas()
        if not function.isEdgeBase():
            result, id, wkt = self.findNearestNode(args, pt)
            if result:
                ids = self.dock.lineEditIds.text()
                if not ids:
                    self.dock.lineEditIds.setText(str(id))
                else:
                    self.dock.lineEditIds.setText(ids + "," + str(id))
                geom = QgsGeometry().fromWkt(wkt)
                vertexMarker = QgsVertexMarker(mapCanvas)
                vertexMarker.setColor(Qt.green)
                vertexMarker.setPenWidth(2)
                vertexMarker.setCenter(geom.asPoint())
                self.idsVertexMarkers.append(vertexMarker)
        else:
            result, id, wkt, pos, pointWkt = self.findNearestLink(args, pt)
            if result:
                ids = self.dock.lineEditIds.text()
                if not ids:
                    self.dock.lineEditIds.setText(str(id))
                else:
                    self.dock.lineEditIds.setText(ids + "," + str(id))
                geom = QgsGeometry().fromWkt(wkt)
                idRubberBand = QgsRubberBand(mapCanvas, Utils.getRubberBandType(False))
                idRubberBand.setColor(Qt.yellow)
                idRubberBand.setWidth(4)
                if geom.wkbType() == QGis.WKBMultiLineString:
                    for line in geom.asMultiPolyline():
                        for pt in line:
                            idRubberBand.addPoint(pt)
                elif geom.wkbType() == QGis.WKBLineString:
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
        if checked:
            self.toggleSelectButton(self.dock.buttonSelectSourceId)
            self.dock.lineEditSourceId.setText("")
            self.sourceIdVertexMarker.setVisible(False)
            self.sourceIdRubberBand.reset(Utils.getRubberBandType(False))
            self.iface.mapCanvas().setMapTool(self.sourceIdEmitPoint)
        else:
            self.iface.mapCanvas().unsetMapTool(self.sourceIdEmitPoint)
        
    def setSourceId(self, pt):
        function = self.functions[str(self.dock.comboBoxFunction.currentText())]
        args = self.getBaseArguments()
        if not function.isEdgeBase():
            result, id, wkt = self.findNearestNode(args, pt)
            if result:
                self.dock.lineEditSourceId.setText(str(id))
                geom = QgsGeometry().fromWkt(wkt)
                self.sourceIdVertexMarker.setCenter(geom.asPoint())
                self.sourceIdVertexMarker.setVisible(True)
                self.dock.buttonSelectSourceId.click()
        else:
            result, id, wkt, pos, pointWkt = self.findNearestLink(args, pt)
            if result:
                self.dock.lineEditSourceId.setText(str(id))
                geom = QgsGeometry().fromWkt(wkt)
                if geom.wkbType() == QGis.WKBMultiLineString:
                    for line in geom.asMultiPolyline():
                        for pt in line:
                            self.sourceIdRubberBand.addPoint(pt)
                elif geom.wkbType() == QGis.WKBLineString:
                    for pt in geom.asPolyline():
                        self.sourceIdRubberBand.addPoint(pt)
                self.dock.lineEditSourcePos.setText(str(pos))
                pointGeom = QgsGeometry().fromWkt(pointWkt)
                self.sourceIdVertexMarker.setCenter(pointGeom.asPoint())
                self.sourceIdVertexMarker.setVisible(True)
                self.dock.buttonSelectSourceId.click()
        Utils.refreshMapCanvas(self.iface.mapCanvas())
        
        
    def selectSourceIds(self, checked):
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
        args = self.getBaseArguments()
        result, id, wkt = self.findNearestNode(args, pt)
        if result:
            ids = self.dock.lineEditSourceIds.text()
            if not ids:
                self.dock.lineEditSourceIds.setText(str(id))
            else:
                self.dock.lineEditSourceIds.setText(ids + "," + str(id))
            geom = QgsGeometry().fromWkt(wkt)
            mapCanvas = self.iface.mapCanvas()
            vertexMarker = QgsVertexMarker(mapCanvas)
            vertexMarker.setColor(Qt.blue)
            vertexMarker.setPenWidth(2)
            vertexMarker.setCenter(geom.asPoint())
            self.sourceIdsVertexMarkers.append(vertexMarker)
            Utils.refreshMapCanvas(mapCanvas)


    def selectTargetId(self, checked):
        if checked:
            self.toggleSelectButton(self.dock.buttonSelectTargetId)
            self.dock.lineEditTargetId.setText("")
            self.targetIdVertexMarker.setVisible(False)
            self.targetIdRubberBand.reset(Utils.getRubberBandType(False))
            self.iface.mapCanvas().setMapTool(self.targetIdEmitPoint)
        else:
            self.iface.mapCanvas().unsetMapTool(self.targetIdEmitPoint)
        
    def setTargetId(self, pt):
        function = self.functions[str(self.dock.comboBoxFunction.currentText())]
        args = self.getBaseArguments()
        if not function.isEdgeBase():
            result, id, wkt = self.findNearestNode(args, pt)
            if result:
                self.dock.lineEditTargetId.setText(str(id))
                geom = QgsGeometry().fromWkt(wkt)
                self.targetIdVertexMarker.setCenter(geom.asPoint())
                self.targetIdVertexMarker.setVisible(True)
                self.dock.buttonSelectTargetId.click()
        else:
            result, id, wkt, pos, pointWkt = self.findNearestLink(args, pt)
            if result:
                self.dock.lineEditTargetId.setText(str(id))
                geom = QgsGeometry().fromWkt(wkt)
                if geom.wkbType() == QGis.WKBMultiLineString:
                    for line in geom.asMultiPolyline():
                        for pt in line:
                            self.targetIdRubberBand.addPoint(pt)
                elif geom.wkbType() == QGis.WKBLineString:
                    for pt in geom.asPolyline():
                        self.targetIdRubberBand.addPoint(pt)
                self.dock.lineEditTargetPos.setText(str(pos))
                pointGeom = QgsGeometry().fromWkt(pointWkt)
                self.targetIdVertexMarker.setCenter(pointGeom.asPoint())
                self.targetIdVertexMarker.setVisible(True)
                self.dock.buttonSelectTargetId.click()
        Utils.refreshMapCanvas(self.iface.mapCanvas())
        
    def selectTargetIds(self, checked):
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
        args = self.getBaseArguments()
        result, id, wkt = self.findNearestNode(args, pt)
        if result:
            ids = self.dock.lineEditTargetIds.text()
            if not ids:
                self.dock.lineEditTargetIds.setText(str(id))
            else:
                self.dock.lineEditTargetIds.setText(ids + "," + str(id))
            geom = QgsGeometry().fromWkt(wkt)
            mapCanvas = self.iface.mapCanvas()
            vertexMarker = QgsVertexMarker(mapCanvas)
            vertexMarker.setColor(Qt.green)
            vertexMarker.setPenWidth(2)
            vertexMarker.setCenter(geom.asPoint())
            self.targetIdsVertexMarkers.append(vertexMarker)
            Utils.refreshMapCanvas(mapCanvas)
        
    def updateReverseCostEnabled(self, state):
        if state == Qt.Checked:
            self.dock.lineEditReverseCost.setEnabled(True)
        else:
            self.dock.lineEditReverseCost.setEnabled(False)
        
    def run(self):
        """ Draws a Preview on the canvas"""
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        
        function = self.functions[str(self.dock.comboBoxFunction.currentText())]
        args = self.getArguments(function.getControlNames(self.version))
        
        empties = []
        for key in args.keys():
            if not args[key]:
                empties.append(key)
        
        if len(empties) > 0:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self.dock, self.dock.windowTitle(),
                'Following argument is not specified.\n' + ','.join(empties))
            return
        
        db = None
        try:
            dbname = str(self.dock.comboConnections.currentText())
            db = self.actionsDb[dbname].connect()
            
            con = db.con
            
            version = Utils.getPgrVersion(con)
            args['version'] = version
            
            srid, geomType = Utils.getSridAndGeomType(con, args['edge_table'], args['geometry'])
            if (function.getName() == 'tsp(euclid)'):
                args['node_query'] = Utils.getNodeQuery(args, geomType)
            
            function.prepare(self.canvasItemList)
            
            args['BBOX'], args['printBBOX'] = self.getBBOX(srid) 
            query = function.getQuery(args)
            #QMessageBox.information(self.dock, self.dock.windowTitle(), 'Geometry Query:' + query)
           
            cur = con.cursor()
            cur.execute(query)
            rows = cur.fetchall()
            if  len(rows) == 0:
                QMessageBox.information(self.dock, self.dock.windowTitle(), 'No paths found in ' + self.getLayerName(args))
            
            args['srid'] = srid
            args['canvas_srid'] = Utils.getCanvasSrid(Utils.getDestinationCrs(self.iface.mapCanvas()))
            Utils.setTransformQuotes(args, srid, args['canvas_srid'])
            function.draw(rows, con, args, geomType, self.canvasItemList, self.iface.mapCanvas())
            
        except psycopg2.DatabaseError, e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)
            
        except SystemError, e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)
            
        except AssertionError, e:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self.dock, self.dock.windowTitle(), '%s' % e)
            
        finally:
            QApplication.restoreOverrideCursor()
            if db and db.con:
                try:
                    db.con.close()
                except:
                    QMessageBox.critical(self.dock, self.dock.windowTitle(),
                        'server closed the connection unexpectedly')

    def export(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        
        function = self.functions[str(self.dock.comboBoxFunction.currentText())]
        args = self.getArguments(function.getControlNames(self.version))
        
        empties = []
        for key in args.keys():
            if not args[key]:
                empties.append(key)
        
        if len(empties) > 0:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self.dock, self.dock.windowTitle(),
                'Following argument is not specified.\n' + ','.join(empties))
            return
        
        db = None
        try:
            dbname = str(self.dock.comboConnections.currentText())
            db = self.actionsDb[dbname].connect()
            
            con = db.con
            
            version = Utils.getPgrVersion(con)

            args['version'] = version
            if (self.version!=version) :
                QMessageBox.warning(self.dock, self.dock.windowTitle(),
                  'versions are different')


            srid, geomType = Utils.getSridAndGeomType(con, '%(edge_table)s' % args, '%(geometry)s' % args)
            args['BBOX'], args['printBBOX'] = self.getBBOX(srid) 

            #get the EXPORT query
            msgQuery = function.getExportQuery(args)
            #QMessageBox.information(self.dock, self.dock.windowTitle(), 'Geometry Query:\n' + msgQuery)
            Utils.logMessage('Export:\n' + msgQuery)
            
            query = self.cleanQuery(msgQuery)
            
            uri = db.getURI()
            uri.setDataSource("", "(" + query + ")", "path_geom", "", "seq")
            
            layerName = self.getLayerName(args)

            vl = self.iface.addVectorLayer(uri.uri(), layerName, db.getProviderName())
            if not vl:
                QMessageBox.information(self.dock, self.dock.windowTitle(), 'Invalid Layer:\n - No paths found or\n - Failed to create vector layer from query')
                #QMessageBox.information(self.dock, self.dock.windowTitle(), 'pgRouting Query:' + function.getQuery(args))
                #QMessageBox.information(self.dock, self.dock.windowTitle(), 'Geometry Query:' + msgQuery)
            
        except psycopg2.DatabaseError, e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)
            
        except SystemError, e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)
            
        finally:
            QApplication.restoreOverrideCursor()
            if db and db.con:
                try:
                    db.con.close()
                except:
                    QMessageBox.critical(self.dock, self.dock.windowTitle(),
                        'server closed the connection unexpectedly')

    def cleanQuery(self, msgQuery):
        query = msgQuery.replace('\n', ' ')
        query = re.sub(r'\s+', ' ', query)
        query = query.replace('( ', '(')
        query = query.replace(' )', ')')
        query = query.strip()
        return query

    def getBBOX(self, srid):
        """ Returns the (Ready to use in query BBOX , print BBOX) """
        bbox = {}
        bbox['srid'] = srid
        bbox['xMin'] = self.iface.mapCanvas().extent().xMinimum()
        bbox['yMin'] = self.iface.mapCanvas().extent().yMinimum()
        bbox['xMax'] = self.iface.mapCanvas().extent().xMaximum()
        bbox['yMax'] = self.iface.mapCanvas().extent().yMaximum()
        text = "BBOX(" + str(round(bbox['xMin'],2))
        text += " " + str(round(bbox['yMin'],2))
        text += "," + str(round(bbox['xMax'],2))
        text += " " + str(round(bbox['yMax'],2)) + ")"
        return """
            ST_MakeEnvelope(
              %(xMin)s, %(yMin)s,
              %(xMax)s, %(yMax)s, %(srid)s
              )
        """ % bbox, text
    
                        
    def exportMerged(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        
        function = self.functions[str(self.dock.comboBoxFunction.currentText())]
        args = self.getArguments(function.getControlNames(self.version))
        
        empties = []
        for key in args.keys():
            if not args[key]:
                empties.append(key)
        
        if len(empties) > 0:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self.dock, self.dock.windowTitle(),
                'Following argument is not specified.\n' + ','.join(empties))
            return
        
        db = None
        try:
            dbname = str(self.dock.comboConnections.currentText())
            db = self.actionsDb[dbname].connect()
            
            con = db.con
            
            version = Utils.getPgrVersion(con)
            args['version'] = version
            
            srid, geomType = Utils.getSridAndGeomType(con, '%(edge_table)s' % args, '%(geometry)s' % args)
            args['BBOX'], args['printBBOX'] = self.getBBOX(srid) 

            # get the exportMerge query
            msgQuery = function.getExportMergeQuery(args)
            Utils.logMessage('Export merged:\n' + msgQuery)

            query = self.cleanQuery(msgQuery)
            
            uri = db.getURI()
            uri.setDataSource("", "(" + query + ")", "path_geom", "", "seq")
            
            # add vector layer to map
            layerName = self.getLayerName(args, 'M')
            
            vl = self.iface.addVectorLayer(uri.uri(), layerName, db.getProviderName())
            if not vl:

                bigIntFunctions = [
                    'dijkstra',
                    'drivingDistance',
                    'ksp',
                    'alphaShape'
                ]
                if function.getName() in bigIntFunctions:
                    QMessageBox.information(self.dock, self.dock.windowTitle(), 'Invalid Layer:\n - No paths found')
                else:
                    QMessageBox.information(self.dock, self.dock.windowTitle(), 'Invalid Layer:\n - No paths found or\n - Failed to create vector layer from query')
            
        except psycopg2.DatabaseError, e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)
            
        except SystemError, e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)
            
        finally:
            QApplication.restoreOverrideCursor()
            if db and db.con:
                try:
                    db.con.close()
                except:
                    QMessageBox.critical(self.dock, self.dock.windowTitle(),
                        'server closed the connection unexpectedly')
        
    def getLayerName(self, args, letter=''):
        function = self.functions[str(self.dock.comboBoxFunction.currentText())]

        layerName = "(" + letter 

        if 'directed' in args and args['directed'] == 'true':
            layerName +=  "D) "
        else:
            layerName +=  "U) "

        layerName += function.getName() + ": "


        if 'source_id' in args:
            layerName +=  args['source_id']
        elif 'ids' in args:
            layerName += "{" + args['ids'] + "}"
        else:
            layerName +=  "[" + args['source_ids'] + "]"

        if 'ids' in args:
            layerName += " "
        elif 'distance' in args:
            layerName += " dd = " + args['distance']
        else:
            layerName += " to "
            if 'target_id' in args:
                layerName += args['target_id']
            else:
                layerName += "[" + args['target_ids'] + "]"

        if 'paths' in args:
            layerName +=  " -  K = " + args['paths']
            if 'heap_paths' in args and args['heap_paths'] == 'true':
                layerName += '+'
        layerName += " " +  args['printBBOX']

        return layerName
            



    def clear(self):
        #self.dock.lineEditIds.setText("")
        for marker in self.idsVertexMarkers:
            marker.setVisible(False)
        self.idsVertexMarkers = []

        #self.dock.lineEditSourceIds.setText("")
        for marker in self.sourceIdsVertexMarkers:
            marker.setVisible(False)
        self.sourceIdsVertexMarkers = []

        #self.dock.lineEditTargetIds.setText("")
        for marker in self.targetIdsVertexMarkers:
            marker.setVisible(False)
        self.targetIdsVertexMarkers = []

        #self.dock.lineEditPcts.setText("")
        #self.dock.lineEditSourceId.setText("")
        self.sourceIdVertexMarker.setVisible(False)
        #self.dock.lineEditSourcePos.setText("0.5")
        #self.dock.lineEditTargetId.setText("")
        self.targetIdVertexMarker.setVisible(False)
        #self.dock.lineEditTargetPos.setText("0.5")
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
            except RuntimeError, e:
                Utils.logMessage("anno.setVisible(False) failed, " + e.message, QgsMessageLog.WARNING)
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
        
    def getArguments(self, controls):
        args = {}
        args['edge_table'] = self.dock.lineEditTable.text()
        args['geometry'] = self.dock.lineEditGeometry.text()
        if 'lineEditId' in controls:
            args['id'] = self.dock.lineEditId.text()

        if 'lineEditSource' in controls:
            args['source'] = self.dock.lineEditSource.text()
        
        if 'lineEditTarget' in controls:
            args['target'] = self.dock.lineEditTarget.text()
        
        if 'lineEditCost' in controls:
            args['cost'] = self.dock.lineEditCost.text()
        
        if 'lineEditReverseCost' in controls:
            args['reverse_cost'] = self.dock.lineEditReverseCost.text()
        
        if 'lineEditX1' in controls:
            args['x1'] = self.dock.lineEditX1.text()
        
        if 'lineEditY1' in controls:
            args['y1'] = self.dock.lineEditY1.text()
        
        if 'lineEditX2' in controls:
            args['x2'] = self.dock.lineEditX2.text()
        
        if 'lineEditY2' in controls:
            args['y2'] = self.dock.lineEditY2.text()
        
        if 'lineEditRule' in controls:
            args['rule'] = self.dock.lineEditRule.text()
        
        if 'lineEditToCost' in controls:
            args['to_cost'] = self.dock.lineEditToCost.text()
        
        if 'lineEditIds' in controls:
            args['ids'] = self.dock.lineEditIds.text()

        if 'lineEditPcts' in controls:
            args['pcts'] = self.dock.lineEditPcts.text()

        if 'lineEditSourceId' in controls:
            args['source_id'] = self.dock.lineEditSourceId.text()
        
        if 'lineEditSourcePos' in controls:
            args['source_pos'] = self.dock.lineEditSourcePos.text()
        
        if 'lineEditSourceIds' in controls:
            args['source_ids'] = self.dock.lineEditSourceIds.text()
        
        if 'lineEditTargetId' in controls:
            args['target_id'] = self.dock.lineEditTargetId.text()
        
        if 'lineEditTargetPos' in controls:
            args['target_pos'] = self.dock.lineEditTargetPos.text()
        
        if 'lineEditTargetIds' in controls:
            args['target_ids'] = self.dock.lineEditTargetIds.text()
        
        if 'lineEditDistance' in controls:
            args['distance'] = self.dock.lineEditDistance.text()
        
        if 'lineEditAlpha' in controls:
            args['alpha'] = self.dock.lineEditAlpha.text()
        
        if 'lineEditPaths' in controls:
            args['paths'] = self.dock.lineEditPaths.text()
        
        if 'checkBoxDirected' in controls:
            args['directed'] = str(self.dock.checkBoxDirected.isChecked()).lower()
        
        if 'checkBoxHeapPaths' in controls:
            args['heap_paths'] = str(self.dock.checkBoxHeapPaths.isChecked()).lower()
        
        if 'checkBoxHasReverseCost' in controls:
            args['has_reverse_cost'] = str(self.dock.checkBoxHasReverseCost.isChecked()).lower()
            if args['has_reverse_cost'] == 'false':
                args['reverse_cost'] = ' '
            else:
                args['reverse_cost'] = ', ' + args['reverse_cost'] + '::float8 AS reverse_cost'
        
        if 'plainTextEditTurnRestrictSql' in controls:
            args['turn_restrict_sql'] = self.dock.plainTextEditTurnRestrictSql.toPlainText()
        
        return args
        
    def getBaseArguments(self):
        args = {}
        args['edge_table'] = self.dock.lineEditTable.text()
        args['geometry'] = self.dock.lineEditGeometry.text()
        args['id'] = self.dock.lineEditId.text()
        args['source'] = self.dock.lineEditSource.text()
        args['target'] = self.dock.lineEditTarget.text()
        
        empties = []
        for key in args.keys():
            if not args[key]:
                empties.append(key)
        
        if len(empties) > 0:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self.dock, self.dock.windowTitle(),
                'Following argument is not specified.\n' + ','.join(empties))
            return None
        
        return args
        
        
    # emulate "matching.sql" - "find_nearest_node_within_distance"
    def findNearestNode(self, args, pt):
        distance = self.iface.mapCanvas().getCoordinateTransform().mapUnitsPerPixel() * self.FIND_RADIUS
        rect = QgsRectangle(pt.x() - distance, pt.y() - distance, pt.x() + distance, pt.y() + distance)
        canvasCrs = Utils.getDestinationCrs(self.iface.mapCanvas())
        db = None
        try:
            dbname = str(self.dock.comboConnections.currentText())
            db = self.actionsDb[dbname].connect()
            
            con = db.con
            #srid, geomType = self.getSridAndGeomType(con, args)
            #srid, geomType = Utils.getSridAndGeomType(con, args['edge_table'], args['geometry'])
            srid, geomType = Utils.getSridAndGeomType(con, '%(edge_table)s' % args, '%(geometry)s' % args)
            if self.iface.mapCanvas().hasCrsTransformEnabled():
                layerCrs = QgsCoordinateReferenceSystem()
                Utils.createFromSrid(layerCrs, srid)
                trans = QgsCoordinateTransform(canvasCrs, layerCrs)
                pt = trans.transform(pt)
                rect = trans.transform(rect)
            
            args['canvas_srid'] = Utils.getCanvasSrid(canvasCrs)
            args['srid'] = srid
            args['x'] = pt.x()
            args['y'] = pt.y()
            args['minx'] = rect.xMinimum()
            args['miny'] = rect.yMinimum()
            args['maxx'] = rect.xMaximum()
            args['maxy'] = rect.yMaximum()
            
            Utils.setStartPoint(geomType, args)
            Utils.setEndPoint(geomType, args)
            #Utils.setTransformQuotes(args)
            Utils.setTransformQuotes(args, srid, args['canvas_srid'])
            
            # Getting nearest source
            query1 = """
            SELECT %(source)s,
                ST_Distance(
                    %(startpoint)s,
                    ST_GeomFromText('POINT(%(x)f %(y)f)', %(srid)d)
                ) AS dist,
                ST_AsText(%(transform_s)s%(startpoint)s%(transform_e)s)
                FROM %(edge_table)s
                WHERE ST_SetSRID('BOX3D(%(minx)f %(miny)f, %(maxx)f %(maxy)f)'::BOX3D, %(srid)d)
                    && %(geometry)s ORDER BY dist ASC LIMIT 1""" % args
            
            ##Utils.logMessage(query1)
            cur1 = con.cursor()
            cur1.execute(query1)
            row1 = cur1.fetchone()
            d1 = None
            source = None
            wkt1 = None
            if row1:
                d1 = row1[1]
                source = row1[0]
                wkt1 = row1[2]
            
            # Getting nearest target
            query2 = """
            SELECT %(target)s,
                ST_Distance(
                    %(endpoint)s,
                    ST_GeomFromText('POINT(%(x)f %(y)f)', %(srid)d)
                ) AS dist,
                ST_AsText(%(transform_s)s%(endpoint)s%(transform_e)s)
                FROM %(edge_table)s
                WHERE ST_SetSRID('BOX3D(%(minx)f %(miny)f, %(maxx)f %(maxy)f)'::BOX3D, %(srid)d)
                    && %(geometry)s ORDER BY dist ASC LIMIT 1""" % args
            
            ##Utils.logMessage(query2)
            cur2 = con.cursor()
            cur2.execute(query2)
            row2 = cur2.fetchone()
            d2 = None
            target = None
            wkt2 = None
            if row2:
                d2 = row2[1]
                target = row2[0]
                wkt2 = row2[2]
            
            # Checking what is nearer - source or target
            d = None
            node = None
            wkt = None
            if d1 and (not d2):
                node = source
                d = d1
                wkt = wkt1
            elif (not d1) and d2:
                node = target
                d = d2
                wkt = wkt2
            elif d1 and d2:
                if d1 < d2:
                    node = source
                    d = d1
                    wkt = wkt1
                else:
                    node = target
                    d = d2
                    wkt = wkt2
            
            ##Utils.logMessage(str(d))
            if (d == None) or (d > distance):
                node = None
                wkt = None
                return False, None, None
            
            return True, node, wkt
            
        except psycopg2.DatabaseError, e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)
            return False, None, None
            
        finally:
            if db and db.con:
                db.con.close()
        
    # emulate "matching.sql" - "find_nearest_link_within_distance"
    def findNearestLink(self, args, pt):
        distance = self.iface.mapCanvas().getCoordinateTransform().mapUnitsPerPixel() * self.FIND_RADIUS
        rect = QgsRectangle(pt.x() - distance, pt.y() - distance, pt.x() + distance, pt.y() + distance)
        canvasCrs = Utils.getDestinationCrs(self.iface.mapCanvas())
        db = None
        try:
            dbname = str(self.dock.comboConnections.currentText())
            db = self.actionsDb[dbname].connect()
            
            con = db.con
            cur = con.cursor()

            srid, geomType = Utils.getSridAndGeomType(con, '%(edge_table)s' % args, '%(geometry)s' % args)

            if self.iface.mapCanvas().hasCrsTransformEnabled():
                layerCrs = QgsCoordinateReferenceSystem()
                Utils.createFromSrid(layerCrs, srid)
                trans = QgsCoordinateTransform(canvasCrs, layerCrs)
                pt = trans.transform(pt)
                rect = trans.transform(rect)
            
            args['canvas_srid'] = Utils.getCanvasSrid(canvasCrs)
            args['srid'] = srid
            args['x'] = pt.x()
            args['y'] = pt.y()
            args['minx'] = rect.xMinimum()
            args['miny'] = rect.yMinimum()
            args['maxx'] = rect.xMaximum()
            args['maxy'] = rect.yMaximum()
            args['decimal_places'] = self.FRACTION_DECIMAL_PLACES
            
            #Utils.setTransformQuotes(args)
            Utils.setTransformQuotes(args, srid, args['canvas_srid'])
            
            # Searching for a link within the distance
            query = """
            WITH point AS (
                SELECT ST_GeomFromText('POINT(%(x)f %(y)f)', %(srid)d) AS geom
            )
            SELECT %(id)s,
                ST_Distance(%(geometry)s, point.geom) AS dist,
                ST_AsText(%(transform_s)s%(geometry)s%(transform_e)s) AS wkt,
                ROUND(ST_Line_Locate_Point(%(geometry)s, point.geom)::numeric, %(decimal_places)d) AS pos,
                ST_AsText(%(transform_s)sST_Line_Interpolate_point(%(geometry)s,
                    ROUND(ST_Line_Locate_Point(%(geometry)s, point.geom)::numeric, %(decimal_places)d))%(transform_e)s) AS pointWkt
                FROM %(edge_table)s, point
                WHERE ST_SetSRID('BOX3D(%(minx)f %(miny)f, %(maxx)f %(maxy)f)'::BOX3D, %(srid)d)
                    && %(geometry)s ORDER BY dist ASC LIMIT 1""" % args
            
            ##Utils.logMessage(query)
            cur = con.cursor()
            cur.execute(query)
            row = cur.fetchone()
            if not row:
                return False, None, None
            link = row[0]
            wkt = row[2]
            pos = row[3]
            pointWkt = row[4]
            
            return True, link, wkt, pos, pointWkt
            
        except psycopg2.DatabaseError, e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.dock, self.dock.windowTitle(), '%s' % e)
            return False, None, None
            
        finally:
            if db and db.con:
                db.con.close()
    
    def loadSettings(self):
        settings = QSettings()
        idx = self.dock.comboConnections.findText(Utils.getStringValue(settings, '/pgRoutingLayer/Database', ''))
        if idx >= 0:
            self.dock.comboConnections.setCurrentIndex(idx)
        idx = self.dock.comboBoxFunction.findText(Utils.getStringValue(settings, '/pgRoutingLayer/Function', 'dijkstra'))
        if idx >= 0:
            self.dock.comboBoxFunction.setCurrentIndex(idx)
        
        self.dock.lineEditTable.setText(Utils.getStringValue(settings, '/pgRoutingLayer/sql/edge_table', 'roads'))
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
        self.dock.lineEditRule.setText(Utils.getStringValue(settings, '/pgRoutingLayer/sql/rule', 'rule'))
        self.dock.lineEditToCost.setText(Utils.getStringValue(settings, '/pgRoutingLayer/sql/to_cost', 'to_cost'))
        
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
        self.dock.plainTextEditTurnRestrictSql.setPlainText(Utils.getStringValue(settings, '/pgRoutingLayer/turn_restrict_sql', 'null'))
        
    def saveSettings(self):
        settings = QSettings()
        settings.setValue('/pgRoutingLayer/Database', self.dock.comboConnections.currentText())
        settings.setValue('/pgRoutingLayer/Function', self.dock.comboBoxFunction.currentText())
        
        settings.setValue('/pgRoutingLayer/sql/edge_table', self.dock.lineEditTable.text())
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

        settings.setValue('/pgRoutingLayer/sql/rule', self.dock.lineEditRule.text())
        settings.setValue('/pgRoutingLayer/sql/to_cost', self.dock.lineEditToCost.text())
        
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
        settings.setValue('/pgRoutingLayer/turn_restrict_sql', self.dock.plainTextEditTurnRestrictSql.toPlainText())

