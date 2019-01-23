# Welcome to pgRoutingLayer

A plugin for QGIS created by by Anita Graser, Ko Nagase and Vicky Vergara.

pgRoutingLayer is currently developed and maintained by pgRouting community.

- Project home and bug tracker: [https://github.com/pgrouting/pgRoutingLayer](https://github.com/pgrouting/pgRoutingLayer)
- Plugin repository: [https://plugins.qgis.org/plugins](https://plugins.qgis.org/plugins)

## What is the goal

PgRouting Layer is a plugin for QGIS that serves as a GUI for pgRouting - a popular routing solution for PostGIS databases.

## What this plugin currently does

Please check the pgRouting documentation for detailed descriptons: [http://docs.pgrouting.org](http://docs.pgrouting.org)

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


## License

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

## Installation

This plugin can be installed using the QGIS Plugin Manager. You will have to enable "experimental" plugins.

### Dependencies

pgRouting v2.x up and running to use this plugin.

Additionally, QGIS needs python-psycopg2 installed to be able to connect to the database.
