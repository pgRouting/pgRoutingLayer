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

- [pgr_dijkstra](functions/pgr_dijkstra.md)
- [pgr_aStar](functions/pgr_aStar.md)
- [pgr_astarCost](functions/pgr_astarCost.md)
- [pgr_bdAstar](functions/pgr_bdAstar.md)
- [pgr_bdAstarCost](functions/pgr_bdAstar.md)
- [pgr_bdDijkstra](functions/pgr_bdDijkstra.md)
- [pgr_bdDijkstraCost](functions/pgr_bdDijkstraCost.md)
- [pgr_djikstra](functions/pgr_dijkstra.md)
- [pgr_djikstraCost](functions/pgr_dijkstraCost.md)
- [pgr_KSP](functions/pgr_KSP.md)

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
