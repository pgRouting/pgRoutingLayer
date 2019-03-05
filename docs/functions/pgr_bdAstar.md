<pgRoutingLayer Manual>
<Copyright(c) pgRouting Contributors>
<This documentation is licensed under a Creative Commons Attribution-Share>
<Alike 3.0 License: http://creativecommons.org/licenses/by-sa/3.0/>

# pgr_bdAstar
![pgr_bdAstar](../img/functions/f_pgr_bdAstar.png)

|Button|Action|
| ----------- | --------- |
|![Help](../img/functions/helpButton.png)|Opens the web page of the documentation of pgr_bdAstar|
|![Function](../img/functions/bdAstar.png)| Choose pgr_bdAstar on the drop down box|

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
|![Heuristic](../img/fields/arguments/astar_heuristic.png)| Heuristic number. Current valid values `0~5` . Default ``5``|
|![Factor](../img/fields/arguments/astar_factor.png)| For units manipulation.  `factor > 0`.  Default  ``1``. See  `astar_factor`.|
|![Epsilon](../img/fields/arguments/astar_epsilon.png)| For less restricted results. `epsilon >= 1`.  Default ``1``.|
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
(<U|D>) pgr_bdAstar: <source_id>  to <target_id>  BBOX(<bbox>)
(M <U|D>) pgr_bdAstar: <source_id>  to <target_id>  BBOX(<bbox>)
```