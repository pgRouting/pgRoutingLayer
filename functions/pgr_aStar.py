from __future__ import absolute_import
from pgRoutingLayer import pgRoutingLayer_utils as Utils
from .AstarBase import AstarBase
from psycopg2 import sql

class Function(AstarBase):

    minPGRversion = 2.4

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'pgr_astar'

    def __init__(self, ui):
        AstarBase.__init__(self, ui)
