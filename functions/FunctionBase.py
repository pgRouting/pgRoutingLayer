
class FunctionBase(object):

    # the mayority of the functions have this values
    exportButton = True
    exportMergeButton = True
    exportEdgeBase = False

    @classmethod
    def getName(self):
        return ''
    
    @classmethod
    def getControlNames(self, version):
        return [ '' ]
    
    @classmethod
    def isEdgeBase(self):
        return self.exportEdgeBase
    
    @classmethod
    def canExport(self):
        return self.exportButton

    @classmethod
    def canExportMerged(self):
        return self.exportMergeButton

    @classmethod
    def isSupportedVersion(self, version):
        return version >= 2.0 and version < 3.0

    @classmethod
    def whereClause(self, table, geometry, bbox):
        if bbox == ' ':
            return ' '
        else:
            return 'WHERE {1}.{2} {3}'.format(table, geometry, bbox)

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

        args['one_geom_query'] = """
            SELECT ST_LineMerge(ST_Union(path_geom)) AS path_geom
            FROM with_geom
            """

        args['aggregates_query'] = """SELECT
            SUM(_cost) AS agg_cost,
            array_agg(_node ORDER BY seq) AS _nodes,
            array_agg(_edge ORDER BY seq) AS _edges
            FROM result
            """

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

    def __init__(self, ui):
        self.ui = ui
        self.minVersion = 2.0
        self.maxVersion = 2.99
