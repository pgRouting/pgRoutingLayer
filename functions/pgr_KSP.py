# -*- coding: utf-8 -*-
# /*PGR-GNU*****************************************************************
# File: pgr_KSP.py
#
# Copyright (c) 2011~2019 pgRouting developers
# Mail: project@pgrouting.org
#
# Developer's GitHub nickname:
# - cayetanobv
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
from psycopg2 import sql
from .FunctionBase import FunctionBase


class Function(FunctionBase):

    minPGRversion = 3.6

    def __init__(self, ui):
        FunctionBase.__init__(self, ui)

    @classmethod
    def isSupportedVersion(self, version):
        ''' Checks supported version '''
        return version >= 3.6

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'pgr_KSP'

    @classmethod
    def getControlNames(self, version):
        ''' returns control names. '''
        return self.commonControls + self.commonBoxes + [
            'labelSourceIds', 'lineEditSourceIds', 'buttonSelectSourceIds',
            'labelTargetIds', 'lineEditTargetIds', 'buttonSelectTargetIds',
            'labelPaths', 'lineEditPaths', 'checkBoxHeapPaths']

    def getQuery(self, args):
        ''' returns the sql query in required signature format of pgr_KSP '''
        return sql.SQL("""
            SELECT seq,
              '(' || start_vid || ',' ||  end_vid || ')-' || path_id AS path_name,
              path_seq AS _path_seq,
              start_vid AS _start_vid, end_vid AS _end_vid,
              path_id AS _path_id,
              node AS _node,
              edge AS _edge,
              cost AS _cost
            FROM pgr_KSP(' {innerQuery} ',
                {source_ids}, {target_ids}, {Kpaths}, {directed}, {heap_paths})
            """).format(**args)

    def getExportQuery(self, args):
        return self.getJoinResultWithEdgeTable(args)

    def getExportMergeQuery(self, args):
        return self.getExportManySourceManyTargetMergeQuery(args)

    def draw(self, rows, con, args, geomType, canvasItemList, mapCanvas):
        ''' draw the result '''
        columns = [2, 4, 5]
        self.drawManyPaths(rows, columns, con, args, geomType, canvasItemList, mapCanvas)
