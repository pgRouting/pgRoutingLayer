"""
/*PGR-GNU*****************************************************************
File: query_utils.py

Copyright (c) 2018 pgRouting developers
Mail: project@pgrouting.org

Copyright (c) 2018 Celia Virginia Vergara Castillo
Mail: vicky at georepublic dot de
------
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
********************************************************************PGR-GNU*/
"""

from psycopg2 import sql


def get_innerQuery(args):
    return sql.SQL("""
        SELECT {id} AS id,
                {source} AS source,
                {target} AS target,
                {cost}::FLOAT AS cost,
                {reverse_cost}::FLOAT AS reverse_cost
            FROM {edge_table}
            {where_clause}
        """.replace("\\n", r"\n")).format(**args)

def get_innerQueryXY(args):
    return sql.SQL("""
        SELECT {id} AS id,
                {source} AS source,
                {target} AS target,
                {cost}::FLOAT AS cost,
                {reverse_cost}::FLOAT AS reverse_cost,
                {x1}::FLOAT AS x1,
                {y1}::FLOAT AS y1,
                {x2}::FLOAT AS x2,
                {y2}::FLOAT AS y2
            FROM {edge_table}
            {where_clause}
        """.replace("\\n", r"\n")).format(**args)

