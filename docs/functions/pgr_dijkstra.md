# pgr_dijkstra

- Uses BBOX of the QGIS canvas to limit the resulting path(s):

![BBOX](../img/fields/EdgesSQL_fields/BBOXon.png)

## Edges SQL tab
![Edges SQL tab](../img/tabs/edges_SQL/dijkstra-KSP_edgesSQL.png)

|Field|Action|
| ----------- | --------- |
|![Edge table](../img/fields/EdgesSQL_fields/edge_table.png)| Write the table name of the edges|
|![Edge schema](../img/fields/EdgesSQL_fields/edge_schema.png)|Write the schema of the edge table|
|![Geometry](../img/fields/EdgesSQL_fields/geometry.png)|Write the geometry column name|

## Arguments tab
![Arguments tab](../img/tabs/arguments/arguments_dijkstra.png)

|Field|Action|
| ----------- | --------- |
|![fromVids](../img/fields/arguments/astar-dijkstra_fromVids.png)| Choose or write the comma separated identifiers of the start vertices|
|![toVids](../img/fields/arguments/astar-dijkstra_toVids.png)|Choose or write the comma separated identifiers of the destination vertices|

## Execute tab 
![Execute tab](../img/tabs/execute/execute.png)

|Button|Action|
| ----------- | --------- |
|![Preview](../img/buttons/execute/preview.png)| Draws in the canvas the resulting path |
|![Clear Preview](../img/buttons/execute/clearpreview.png)| Removes from the canvas objects generated with Preview|
|![Export](../img/buttons/execute/export.png)| Creates a one row per edge line geometry layer|
|![Export Merged](../img/buttons/execute/exportmergedON.png)| Creates a one row per path multiline geometry layer. As many rows as needed|

Depending on the pressed button the layer name will be 
```
(<U|D>) pgr_dijkstra: <source_id>  to <target_id>  BBOX(<bbox>)
(M <U|D>) pgr_dijkstra: <source_id>  to <target_id>  BBOX(<bbox>)
```