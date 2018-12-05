# pgRoutingLayer documentation

Welcome to pgRoutingLayer documentation.

## About pgRoutingLayer

pgRoutingLayer is a plugin for QGIS that serves as a GUI for pgRouting - a popular routing solution for PostGIS databases.

## What this plugin currently does

### Introduction

- [Layer Naming Convention](intro/layer_naming_convention.md)
- [Main buttons](intro/buttons.md)

### Functions

pgRoutingLayer currently supports the following functions:

- [pgr_alphaShape](functions/pgr_alphaShape.md)
- [pgr_astar](functions/pgr_astar.md)
- [pgr_bdAstar](functions/pgr_bdAstar.md)
- [pgr_bdDijkstra](functions/pgr_bdDijkstra.md)
- [pgr_dijkstra](functions/pgr_dijkstra.md)
- [pgr_drivingDistance](functions/pgr_drivingDistance.md)
- [pgr_KSP](functions/pgr_KSP.md)
- [pgr_trsp(edge)](functions/pgr_trsp_edge.md)
- [pgr_trsp(vertex)](functions/pgr_trsp_vertex.md)
- [pgr_trspViaEdges](functions/pgr_trspViaEdges.md)
- [pgr_trspViaVertices](functions/pgr_trspViaVertices.md)

Please check the pgRouting documentation for detailed descriptons: [https://docs.pgrouting.org](https://docs.pgrouting.org)

## Installation

This plugin can be installed using the QGIS Plugin Manager. You will have to enable "experimental" plugins.

### Dependencies

- This plugin runs only with QGIS 3.x and Python 3.
- pgRouting v2.x up and running to use this plugin.
- Additionally, QGIS needs python-psycopg2 installed to be able to connect to the database.

## Links

- Project home and bug tracker: [https://github.com/pgrouting/pgRoutingLayer](https://github.com/pgrouting/pgRoutingLayer)
- Plugin repository: [https://plugins.qgis.org/plugins](https://plugins.qgis.org/plugins)
- pgRouting project: [https://docs.pgrouting.org](https://docs.pgrouting.org)

## License

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.
