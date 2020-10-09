# Welcome to pgRoutingLayer

A plugin for QGIS created by by Anita Graser, Ko Nagase and Vicky Vergara.

pgRoutingLayer is currently developed and maintained by pgRouting community.

- Project home and bug tracker: [https://github.com/pgrouting/pgRoutingLayer](https://github.com/pgrouting/pgRoutingLayer)
- Plugin repository: [https://plugins.qgis.org/plugins/pgRoutingLayer/](https://plugins.qgis.org/plugins/pgRoutingLayer/)

## What is the goal

PgRouting Layer is a plugin for QGIS that serves as a GUI for pgRouting - a popular routing solution for PostGIS databases.

## What this plugin currently does

Please check plugin documentation for detailed descriptions: [http://qgis.pgrouting.org](http://qgis.pgrouting.org)

pgRoutingLayer currently supports the following functions:

- `pgr_aStar`
- `pgr_aStarCost`
- `pgr_bdAstar`
- `pgr_bdAstarCost`
- `pgr_bdDijkstra`
- `pgr_bdDijkstraCost`
- `pgr_dijkstra`
- `pgr_dijkstraCost`
- `pgr_KSP`

Functions detailed descriptions: [http://docs.pgrouting.org](http://docs.pgrouting.org)


## License

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

## Installation

This plugin can be installed using the QGIS Plugin Manager.

### Dependencies

pgRouting v3.x up and running to use this plugin.

Additionally, QGIS needs python3-psycopg2 installed to be able to connect to the database.
