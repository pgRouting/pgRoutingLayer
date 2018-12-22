from __future__ import absolute_import

from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsPoint, Qgis, QgsProject
from pgRoutingLayer import pgRoutingLayer_utils as Utils
from .FunctionBase import FunctionBase

class Function(FunctionBase):

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'pgr_alphaShape'

    @classmethod
    def getControlNames(self, version):
        ''' returns control names for this function. '''
        self.version = version
        return self.commonControls + self.commonBoxes + [
            'labelId', 'lineEditId',
            'labelSource', 'lineEditSource',
            'labelTarget', 'lineEditTarget',
            'labelCost', 'lineEditCost',
            'labelReverseCost', 'lineEditReverseCost',
            'labelSourceId', 'lineEditSourceId', 'buttonSelectSourceId',
            'labelDistance', 'lineEditDistance',
            'labelAlpha', 'lineEditAlpha',
            'checkBoxDirected', 'checkBoxHasReverseCost'
        ]

    @classmethod
    def canExportMerged(self):
        return False

    def prepare(self, canvasItemList):
        resultAreaRubberBand = canvasItemList['area']
        resultAreaRubberBand.reset(Utils.getRubberBandType(True))

    def getQuery(self, args):
        ''' returns the sql query for pgr_alphashape '''
        args['where_clause'] = self.whereClause(args['edge_table'], args['geometry'], args['BBOX'])
        if args['version'] < 2.1:
            return """
                SELECT x, y FROM pgr_alphashape($$
                WITH
                dd AS (
                  SELECT seq, id1 AS _node FROM pgr_drivingDistance('
                        SELECT %(id)s::int4 AS id,
                        %(source)s::int4 AS source,
                        %(target)s::int4 AS target,
                        %(cost)s::float8 AS cost%(reverse_cost)s
                        FROM %(edge_table)s
			%(where_clause)s',
                        %(source_id)s, %(distance)s,
                        %(directed)s, %(has_reverse_cost)s)
                ),
                node AS (
                    SELECT dd.seq AS id,
                    ST_X(the_geom) AS x, ST_Y(the_geom) AS y
                    FROM %(edge_table)s_vertices_pgr JOIN dd
                    ON %(edge_table)s_vertices_pgr.id = dd._node
                )
                SELECT * FROM node$$::text)
                """ % args

        # V21.+ has pgr_drivingDistance with big int
        # and pgr_alphaShape has an alpha value
        args['alpha'] = ', ' + str(args['alpha'])
        return """
                SELECT x, y FROM pgr_alphashape($$
                WITH
                dd AS (
                  SELECT seq, node AS _node FROM pgr_drivingDistance('
                        SELECT %(id)s AS id,
                        %(source)s AS source,
                        %(target)s AS target,
                        %(cost)s AS cost%(reverse_cost)s
                        FROM %(edge_table)s
			%(where_clause)s',
                        %(source_id)s, %(distance)s,
                        %(directed)s)
                ),
                node AS (
                    SELECT dd.seq AS id,
                    ST_X(the_geom) AS x, ST_Y(the_geom) AS y
                    FROM %(edge_table)s_vertices_pgr JOIN dd
                    ON %(edge_table)s_vertices_pgr.id = dd._node
                )
                SELECT * FROM node$$::text%(alpha)s)
                """ % args



    def getExportQuery(self, args):
        if args['version'] < 2.1:
            return """
                SELECT 1 AS seq, ST_SetSRID(pgr_pointsAsPolygon, 0) AS path_geom FROM pgr_pointsAsPolygon($$
                WITH
                dd AS (
                  SELECT seq, id1 AS _node FROM pgr_drivingDistance('
                        SELECT %(id)s::int4 AS id,
                        %(source)s::int4 AS source,
                        %(target)s::int4 AS target,
                        %(cost)s::float8 AS cost%(reverse_cost)s
                        FROM %(edge_table)s
			%(where_clause)s',
                        %(source_id)s, %(distance)s,
                        %(directed)s, %(has_reverse_cost)s)
                ),
                node AS (
                    SELECT dd.seq::int4 AS id,
                    ST_X(the_geom) AS x, ST_Y(the_geom) AS y
                    FROM %(edge_table)s_vertices_pgr JOIN dd
                    ON %(edge_table)s_vertices_pgr.id = dd._node
                )
                SELECT * FROM node$$::text)
                """ % args

        return """
                SELECT 1 AS seq, ST_SetSRID(pgr_pointsAsPolygon, 0) AS path_geom FROM pgr_pointsAsPolygon($$
                WITH
                dd AS (
                  SELECT seq, node AS _node FROM pgr_drivingDistance('
                        SELECT %(id)s AS id,
                        %(source)s AS source,
                        %(target)s AS target,
                        %(cost)s AS cost%(reverse_cost)s
                        FROM %(edge_table)s
			%(where_clause)s',
                        %(source_id)s, %(distance)s,
                        %(directed)s)
                ),
                node AS (
                    SELECT dd.seq::int4 AS id,
                    ST_X(the_geom) AS x, ST_Y(the_geom) AS y
                    FROM %(edge_table)s_vertices_pgr JOIN dd
                    ON %(edge_table)s_vertices_pgr.id = dd._node
                )
                SELECT * FROM node$$::text)
                """ % args



    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        ''' draw the resulting polygon. '''

        resultAreaRubberBand = canvasItemList['area']
        trans = None

        canvasCrs = Utils.getDestinationCrs(mapCanvas)
        layerCrs = QgsCoordinateReferenceSystem()
        Utils.createFromSrid(layerCrs, args['srid'])
        trans = QgsCoordinateTransform(layerCrs, canvasCrs,QgsProject.instance())

        # return columns are 'x', 'y'
        for row in rows:
            x = row[0]
            y = row[1]
            if args['version'] > 2.0 and ((x is None) or (y is None)):
                Utils.logMessage(u'Alpha shape result geometry is MultiPolygon or has holes.\nPlease click [Export] button to see complete result.', level=Qgis.Warning)
                return
            pt = QgsPoint(x, y)
            if trans:
                pt = trans.transform(pt.x(),pt.y())

            resultAreaRubberBand.addPoint(pt)

    def __init__(self, ui):
        FunctionBase.__init__(self, ui)
