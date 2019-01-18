# pgr_astar

- # pgr_astar
![pgr_astar](../img/functions/f_pgr_astar.png)

|Button|Action|
| ----------- | --------- |
|![Help](../img/functions/helpButton.png)|Opens the web page of the documentation of pgr_astar|
|![Function](../img/functions/astar.png)| Choose pgr_astar on the drop down box|

## Edges SQL tab
![Edges SQL tab](../img/tabs/edges_SQL/astar_edgesSQL.png)

|Field|Action|
| ----------- | --------- |
|![Edge table](../img/fields/edgesSQL_fields/edge_table.png)| Write the table name of the edges|
|![Edge schema](../img/fields/edgesSQL_fields/edge_schema.png)|Write the schema of the edge table|
|![Geometry](../img/fields/edgesSQL_fields/geometry.png)|Write the geometry column name|
|![BBOX](../img/fields/edgesSQL_fields/BBOX.png)|Tick to use the  Bounding Box of the QGIS canvas to limit the rows of edge table ![BBOX](../img/fields/edgesSQL_fields/BBOXon.png)|

### Columns

|Field|Action|
| ----------- | --------- |
|![Id](../img/fields/edgesSQL_fields/columns/Id.png)| Write the column that has the edge identifier|
|![Source](../img/fields/edgesSQL_fields/columns/source.png)|Write the column that has the edge source|
|![Target](../img/fields/edgesSQL_fields/columns/target.png)|Write the column that has the edge target|
|![Cost](../img/fields/edgesSQL_fields/columns/cost.png)|Write the column that has the cost of the edge source -> target|
|![Reverse Cost](../img/fields/edgesSQL_fields/columns/reverseCostOFF.png)|Write the column that has the cost of the edge target -> source, the column will be used when the box is ticked ![Reverse Cost](../img/fields/edgesSQL_fields/columns/reverseCost.png)|
|![x](../img/fields/edgesSQL_fields/columns/x1.png)|Write the geometry column name|
|![y](../img/fields/edgesSQL_fields/columns/y1.png)|Write the geometry column name|

## Arguments tab
![Arguments tab](../img/tabs/arguments/arguments_astar.png)

|Field|Action|
| ----------- | --------- |
|![fromVids](../img/fields/arguments/astar-dijkstra_fromVids.png)| Choose with ![plus](../img/tabs/arguments/plus_button.png) or write the comma separated identifiers of the start vertices|
|![toVids](../img/fields/arguments/astar-dijkstra_toVids.png)|Choose with ![plus](../img/tabs/arguments/plus_button.png) or write the comma separated identifiers of the destination vertices|
|![Heuristic](../img/fields/arguments/astar_heuristic.png)| ... |
|![Factor](../img/fields/arguments/astar_factor.png)| ... |
|![Epsilon](../img/fields/arguments/astar_epsilon.png)| ... ![Epsilon](../img/fields/arguments/astar_epsilon2.png)|
|![Directed](../img/fields/arguments/directedOFF.png)| Tick if the graph is directed ![Directed](../img/fields/arguments/directedON.png)|

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
(<U|D>) pgr_astar: <source_id>  to <target_id>  BBOX(<bbox>)
(M <U|D>) pgr_astar: <source_id>  to <target_id>  BBOX(<bbox>)
```