# -*- coding: utf-8 -*-
# /*PGR-GNU*****************************************************************
# File: pgr_bdDijkstraCost.py
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
from .CostBase import CostBase


class Function(CostBase):

    minPGRversion = 2.5

    def __init__(self, ui):
        CostBase.__init__(self, ui)

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'pgr_bdDijkstraCost'
