# coding=utf-8

import logging
import sys

from PyQt4.QtCore import QObject, pyqtSlot, pyqtSignal, QCoreApplication
from qgis.core import QgsMapLayerRegistry, QgsApplication, QgsVectorLayer
from qgis.gui import QgsMapCanvasLayer
import config 



LOGGER = logging.getLogger('QGIS')


def set_up_interface():
    """
    Sets up a QGIS pseudo-application which enables calling methods as if when calling them from QGIS-console.

    :return qgis_app: Pseudo QGIS-instance
    :rtype: QgsApplication
    :return canvas: The map canvas
    :rtype: QgsMapCanvas
    :return iface: A dummy interface, giving access to needed method-calls
    :rtype: QgisInterface
    """
    gui_flag = True  # All test will run qgis in gui mode
    qgis_app = QgsApplication(sys.argv, gui_flag)
    prefix_path = config.qgis_prefix_path()
    qgis_app.setPrefixPath(prefix_path, True)
    qgis_app.initQgis()
    QCoreApplication.setOrganizationName('QGIS')
    QCoreApplication.setApplicationName('QGIS2')

    # parent = QWidget()
    # canvas = QgsMapCanvas(parent)
    # canvas.resize(QSize(400, 400))
    canvas = MyMapCanvas()

    iface = QgisInterface(canvas)

    return qgis_app, canvas, iface

#noinspection PyMethodMayBeStatic,PyPep8Naming
class QgisInterface(QObject):
    """Class to expose QGIS objects and functions to plugins.

    This class is here for enabling us to run unit tests only,
    so most methods are simply stubs.
    """
    currentLayerChanged = pyqtSignal(QgsMapCanvasLayer)

    def __init__(self, canvas):
        """Constructor
        :param canvas:
        """
        QObject.__init__(self)
        self.canvas = canvas
        self.legend_interface = MyLegendInterface()
        self.active_layer = None
        # Set up slots so we can mimic the behaviour of QGIS when layers
        # are added.
        LOGGER.debug('Initialising canvas...')
        # noinspection PyArgumentList
        QgsMapLayerRegistry.instance().layersAdded.connect(self.addLayer)
        # noinspection PyArgumentList
        QgsMapLayerRegistry.instance().layerWasAdded.connect(self.addLayer)
        # noinspection PyArgumentList
        QgsMapLayerRegistry.instance().removeAll.connect(self.removeAllLayers)

        # For processing module
        self.destCrs = None


    @pyqtSlot('QgsMapLayer')
    def addLayer(self, layer):
        """Handle a layer being added to the registry so it shows up in canvas.

        :param layer: list<QgsMapLayer> list of map layers that were added

        .. note: The QgsInterface api does not include this method, it is added
                 here as a helper to facilitate testing.

        .. note: The addLayer method was deprecated in QGIS 1.8 so you should
                 not need this method much.
        """
        # set the recently added layer as active
        # LOGGER.debug('Layer Count Before: %s' % len(self.canvas.layers()))
        current_layers = self.canvas.layers()
        final_layers = [] + current_layers
        final_layers.append(QgsMapCanvasLayer(layer))
        self.canvas.setLayerSet(final_layers)
        self.active_layer = layer

    @pyqtSlot()
    def removeAllLayers(self):
        """Remove layers from the canvas before they get deleted."""
        self.canvas.setLayerSet([])

    def newProject(self):
        """Create new project."""
        # noinspection PyArgumentList
        QgsMapLayerRegistry.instance().removeAllMapLayers()

    def legendInterface(self):
        """Get the legend."""
        return self.legend_interface

    def activeLayer(self):
        """Get pointer to the active layer (layer selected in the legend)."""
        return self.active_layer

    def setActiveLayer(self, layer):
        """Set the given layer as active.
        :param layer: Layer that shall be set active
        :type layer: QgsMapLayer
        """
        self.active_layer = layer

    class actionAddFeature(object):

        def __init__(self):
            pass

        def trigger(self):
            pass

    class actionZoomToLayer(object):

        def __init__(self):
            pass

        def trigger(self):
            pass

    # ---------------- API Mock for QgsInterface follows -------------------
    def zoomFull(self):
        """Zoom to the map full extent."""
        pass

    def zoomToPrevious(self):
        """Zoom to previous view extent."""
        pass

    def zoomToNext(self):
        """Zoom to next view extent."""
        pass

    def zoomToActiveLayer(self):
        """Zoom to extent of active layer."""
        pass

    def addVectorLayer(self, path, base_name, provider_key):
        """Add a vector layer.

        :param path: Path to layer.
        :type path: str

        :param base_name: Base name for layer.
        :type base_name: str

        :param provider_key: Provider key e.g. 'ogr'
        :type provider_key: str
        """
        pass

    def addRasterLayer(self, path, base_name):
        """Add a raster layer given a raster layer file name

        :param path: Path to layer.
        :type path: str

        :param base_name: Base name for layer.
        :type base_name: str
        """
        pass

    def addToolBarIcon(self, action):
        """Add an icon to the plugins toolbar.

        :param action: Action to add to the toolbar.
        :type action: QAction
        """
        pass

    def addPluginToDatabaseMenu(self,name,action):
        """Adds plugin to database menu in QGIS.

        :param name : Name of plugin 
        :type name : str
        :param action: Action to add to the toolbar.
        :type action: QAction
        """
        pass


    def removeToolBarIcon(self, action):
        """Remove an action (icon) from the plugin toolbar.

        :param action: Action to add to the toolbar.
        :type action: QAction
        """
        pass

    def addToolBar(self, name):
        """Add toolbar with specified name.

        :param name: Name for the toolbar.
        :type name: str
        """
        pass

    def mapCanvas(self):
        """Return a pointer to the map canvas."""
        return self.canvas

    def mainWindow(self):
        """Return a pointer to the main window.

        In case of QGIS it returns an instance of QgisApp.
        """
        pass

    def addDockWidget(self, area, dock_widget):
        """Add a dock widget to the main window.

        :param area: Where in the ui the dock should be placed.
        :type area:

        :param dock_widget: A dock widget to add to the UI.
        :type dock_widget: QDockWidget
        """
        pass


class MyLegendInterface(object):

    def __init__(self):
        self.layer_visibility = {}

    def setLayerVisible(self, layer, yes_no):
        self.layer_visibility[layer.name()] = yes_no

    def isLayerVisible(self, layer):
        try:
            return self.layer_visibility[layer.name()]
        except KeyError:
            print('Layer {} has not been set (in)visible yet.'.format(layer.name()))
            return False


class MyMapCanvas(object):

    def __init__(self):
        self.layer_set = []

    def layers(self):
        return self.layer_set

    def layer(self, index):
        layer = self.layer_set[index].layer()
        return layer

    def setLayerSet(self, layer_set):
        self.layer_set = layer_set

    def layerCount(self):
        return len(self.layer_set)


class HybridLayer(QgsVectorLayer):

    def __init__(self, layer_type, layer_name):
        type = '{}?crs=EPSG:3857'.format(layer_type)
        QgsVectorLayer.__init__(self, type, layer_name, 'memory', False)

    def type(self):
        # QgsMapLayer.RasterLayer
        return 1

    def rasterType(self):
        # QgsRasterLayer.Multiband
        return 2

    def bandCount(self):
        # One band for each RGBa
        return 4

    def bandName(self, index):
        return 'Band {}'.format(index)
