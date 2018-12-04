# pgRoutingLayer documentation

Welcome to pgRoutingLayer documentation.


## About pgRoutingLayer

pgRoutingLayer is a plugin for QGIS that serves as a GUI for pgRouting - a popular routing solution for PostGIS databases.

## What this plugin currently does

### Introduction

- [Layer Naming Convention](intro/layer_naming_convention.md)
- [Main buttons](intro/buttons.md)

### Functions

PgRoutingLayer currently supports the following functions:

- [Dijkstra](functions/pgr_dijkstra.md)
- [Astar](functions/pgr_astar.md)
- [bdDijkstra](functions/pgr_bddijkstra.md)
- [bdAstar](functions/pgr_bdastar.md)
- [KSP](functions/pgr_KSP.md)
- [Trsp_vertex](functions/pgr_Trsp_vertex.md)
- [Trsp_edge](functions/Trsp_edge.md)
- [Trsp_via_vertices](functions/Trsp_via_vertices.md)
- [Trsp_via_edges](functions/Trsp_via_edges.md)
- [DrivingDistance](functions/pgr_DrivingDistance.md)
- Alphashape

Please check the pgRouting documentation for detailed descriptons: http://docs.pgrouting.org

## Installation

This plugin can be installed using the QGIS Plugin Manager. You will have to enable "experimental" plugins.

### Dependencies

- This plugin runs only with QGIS 3.x and Python 3.
- pgRouting v2.x up and running to use this plugin.
- Additionally, QGIS needs python-psycopg2 installed to be able to connect to the database.

## Links

- project home and bug tracker: https://github.com/pgrouting/pgRoutingLayer
- plugin repository: http://plugins.qgis.org/plugins
- pgRouting project: https://pgrouting.org


## License

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.
