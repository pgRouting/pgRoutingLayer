# pgr_dijkstra

- Uses BBOX of the QGIS canvas to limit the resulting path(s)

## Edges SQL tab
![Edges SQL tab](../img/tabs/edges_SQL/dijkstra-KSP_edgesSQL.png)

## Arguments tab
![Arguments tab](../img/tabs/arguments/arguments_dijkstra.png)

|Field|Action|
| ----------- | --------- |
|![fromVids](../img/fields/arguments/astar-dijkstra_fromVids.png)| |
|![toVids](../img/fields/arguments/astar-dijkstra_toVids.png)| |

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