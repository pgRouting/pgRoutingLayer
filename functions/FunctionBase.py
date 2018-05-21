from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from .. import pgRoutingLayer_utils as Utils


class FunctionBase(object):

    ''' the mayority of the functions have this values '''
    exportButton = True
    exportMergeButton = True
    exportEdgeBase = False
    commonControls = [
        'labelId',      'lineEditId',
        'labelSource',  'lineEditSource',
        'labelTarget',  'lineEditTarget',
        'labelCost',    'lineEditCost',
        'labelReverseCost', 'lineEditReverseCost']
    commonBoxes = [
            'checkBoxUseBBOX',
            'checkBoxDirected',
            'checkBoxHasReverseCost']
    astarControls = [
            'labelX1', 'lineEditX1',
            'labelY1', 'lineEditY1',
            'labelX2', 'lineEditX2',
            'labelY2', 'lineEditY2']


    @classmethod
    def getName(self):
        return ''

    @classmethod
    def getControlNames(self, version):
        return self.commonControls + self.commonBoxes + [
            'labelSourceIds', 'lineEditSourceIds', 'buttonSelectSourceIds',
            'labelTargetIds', 'lineEditTargetIds', 'buttonSelectTargetIds',
        ]


    ''' checks if EdgeBase is set or not. '''
    @classmethod
    def isEdgeBase(self):
        return self.exportEdgeBase
    ''' checks if exportButton is set or not. '''
    @classmethod
    def canExport(self):
        return self.exportButton

     ''' checks if exportMergeButton is set or not. '''
    @classmethod
    def canExportMerged(self):
        return self.exportMergeButton

     ''' returns true if version is between 2 and 3.0 '''
    @classmethod
    def isSupportedVersion(self, version):
        return version >= 2.0 and version < 3.0

     ''' this function is used for SQL parameterising '''
    @classmethod
    def whereClause(self, table, geometry, bbox):
        if bbox == ' ':   ''' if bounding box is empty return empty. '''
            return ' '
        else:
            return 'WHERE {0}.{1} {2}'.format(table, geometry, bbox)

    def prepare(self, canvasItemList):
        pass

    def getQuery(self, args):
        return ''

    def getExportQuery(self, args):
        return ''

    def getExportMergeQuery(self, args):
        return 'NOT AVAILABLE'

    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        pass


    """ this returns a query which joins edge_table with result based on edge.id and
    then if result._node is equal to source node then it assigns the respective geometry else it reverses the geometry,result is displayed as path_geom """
    def getJoinResultWithEdgeTable(self, args):
        args['result_query'] = self.getQuery(args)

        query = """
            WITH
            result AS ( %(result_query)s )
            SELECT
              CASE
                WHEN result._node = %(edge_table)s.%(source)s
                  THEN %(edge_table)s.%(geometry)s
                ELSE ST_Reverse(%(edge_table)s.%(geometry)s)
              END AS path_geom,
              result.*, %(edge_table)s.*
            FROM %(edge_table)s JOIN result
              ON %(edge_table)s.%(id)s = result._edge ORDER BY result.seq
            """ % args
        return query


    def getExportOneSourceOneTargetMergeQuery(self, args):
        args['result_query'] = self.getQuery(args)

        args['with_geom_query'] = """
            SELECT
              CASE
                WHEN result._node = %(edge_table)s.%(source)s
                  THEN %(edge_table)s.%(geometry)s
                ELSE ST_Reverse(%(edge_table)s.%(geometry)s)
              END AS path_geom
            FROM %(edge_table)s JOIN result
              ON %(edge_table)s.%(id)s = result._edge
            """ % args

          ''' returns a set of multilines sewn together by ST_LineMerge from path_geom. '''
        args['one_geom_query'] = """
            SELECT ST_LineMerge(ST_Union(path_geom)) AS path_geom
            FROM with_geom
            """
            ''' returns total cost as agg_cost,array of concatenated nodes ordered by seq,array of concatenated edges ordered by seq '''
        args['aggregates_query'] = """SELECT
            SUM(_cost) AS agg_cost,
            array_agg(_node ORDER BY seq) AS _nodes,
            array_agg(_edge ORDER BY seq) AS _edges
            FROM result
            """
          ''' gives unique row_number to each row of nodes ,edges originating from them,cost,geometry. '''
        query = """WITH
            result AS ( %(result_query)s ),
            with_geom AS ( %(with_geom_query)s ),
            one_geom AS ( %(one_geom_query)s ),
            aggregates AS ( %(aggregates_query)s )
            SELECT row_number() over() as seq,
            _nodes, _edges, agg_cost, path_geom
            FROM aggregates, one_geom
            """ % args
        return query


    def getExportManySourceManyTargetMergeQuery(self, args):
        args['result_query'] = self.getQuery(args)

        args['with_geom_query'] = """
            SELECT
              seq, result.path_name,
              CASE
                WHEN result._node = %(edge_table)s.%(source)s
                  THEN %(edge_table)s.%(geometry)s
                ELSE ST_Reverse(%(edge_table)s.%(geometry)s)
              END AS path_geom
            FROM %(edge_table)s JOIN result
              ON %(edge_table)s.%(id)s = result._edge
            """ % args

        args['one_geom_query'] = """
            SELECT path_name, ST_LineMerge(ST_Union(path_geom)) AS path_geom
            FROM with_geom
            GROUP BY path_name
            ORDER BY path_name
            """ % args

        args['aggregates_query'] = """
                SELECT
                    path_name, _start_vid, _end_vid,
                    SUM(_cost) AS agg_cost,
                    array_agg(_node ORDER BY _path_seq) AS _nodes,
                    array_agg(_edge ORDER BY _path_seq) AS _edges
                    FROM result
                GROUP BY path_name, _start_vid, _end_vid
                ORDER BY _start_vid, _end_vid"""
''' gives unique row_number to each row having path_name,start_vertex,end_vertex,cost,edges,geometry '''
        query = """WITH
            result AS ( %(result_query)s ),
            with_geom AS ( %(with_geom_query)s ),
            one_geom AS ( %(one_geom_query)s ),
            aggregates AS ( %(aggregates_query)s )
            SELECT row_number() over() as seq,
                path_name, _start_vid, _end_vid, agg_cost, _nodes, _edges,
                path_geom AS path_geom FROM aggregates JOIN one_geom
                USING (path_name)
            """ % args
        return query

''' draws multi line string on the mapCanvas. '''
    def drawManyPaths(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        resultPathsRubberBands = canvasItemList['paths']
        rubberBand = None
        cur_path_id = str(-1) + "," + str(-1)
        for row in rows:
            cur2 = con.cursor()
            args['result_path_id'] = str(row[3]) + "," + str(row[4])
            args['result_node_id'] = row[5]
            args['result_edge_id'] = row[6]
            args['result_cost'] = row[7]
            if args['result_path_id'] != cur_path_id:
                cur_path_id = args['result_path_id']
                if rubberBand:
                    resultPathsRubberBands.append(rubberBand)
                    rubberBand = None

                rubberBand = QgsRubberBand(mapCanvas, Utils.getRubberBandType(False))
                rubberBand.setColor(QColor(255, 0, 0, 128))
                rubberBand.setWidth(4)

            if args['result_edge_id'] != -1:
                query2 = """
                    SELECT ST_AsText(%(transform_s)s%(geometry)s%(transform_e)s) FROM %(edge_table)s
                        WHERE %(source)s = %(result_node_id)d AND %(id)s = %(result_edge_id)d
                    UNION
                    SELECT ST_AsText(%(transform_s)sST_Reverse(%(geometry)s)%(transform_e)s) FROM %(edge_table)s
                        WHERE %(target)s = %(result_node_id)d AND %(id)s = %(result_edge_id)d;
                    """ % args
                ##Utils.logMessage(query2)
                cur2.execute(query2)
                row2 = cur2.fetchone()
                ##Utils.logMessage(str(row2[0]))
                assert row2, "Invalid result geometry. (path_id:%(result_path_id)s, node_id:%(result_node_id)d, edge_id:%(result_edge_id)d)" % args

                geom = QgsGeometry().fromWkt(str(row2[0]))
                if geom.wkbType() == QGis.WKBMultiLineString:
                    for line in geom.asMultiPolyline():
                        for pt in line:
                            rubberBand.addPoint(pt)
                elif geom.wkbType() == QGis.WKBLineString:
                    for pt in geom.asPolyline():
                        rubberBand.addPoint(pt)

        if rubberBand:
            resultPathsRubberBands.append(rubberBand)
            rubberBand = None

''' selects geometry of nodes as text  and then draws line or multilines on the mapCanvas,else throws error message. '''
    def drawOnePath(self, rows, con, args, geomType, canvasItemList, mapCanvas):
            resultPathRubberBand = canvasItemList['path']
            for row in rows:
                cur2 = con.cursor()
                args['result_node_id'] = row[1]
                args['result_edge_id'] = row[2]
                args['result_cost'] = row[3]
                if args['result_edge_id'] != -1:
                    query2 = """
                        SELECT ST_AsText(%(transform_s)s%(geometry)s%(transform_e)s) FROM %(edge_table)s
                            WHERE %(source)s = %(result_node_id)d AND %(id)s = %(result_edge_id)d
                        UNION
                        SELECT ST_AsText(%(transform_s)sST_Reverse(%(geometry)s)%(transform_e)s) FROM %(edge_table)s
                            WHERE %(target)s = %(result_node_id)d AND %(id)s = %(result_edge_id)d;
                    """ % args
                    ##Utils.logMessage(query2)
                    cur2.execute(query2)
                    row2 = cur2.fetchone()
                    ##Utils.logMessage(str(row2[0]))
                    assert row2, "Invalid result geometry. (node_id:%(result_node_id)d, edge_id:%(result_edge_id)d)" % args

                    geom = QgsGeometry().fromWkt(str(row2[0]))
                    if geom.wkbType() == QGis.WKBMultiLineString:
                        for line in geom.asMultiPolyline():
                            for pt in line:
                                resultPathRubberBand.addPoint(pt)
                    elif geom.wkbType() == QGis.WKBLineString:
                        for pt in geom.asPolyline():
                            resultPathRubberBand.addPoint(pt)






    def __init__(self, ui):
        self.ui = ui
        self.minVersion = 2.0
        self.maxVersion = 2.99
