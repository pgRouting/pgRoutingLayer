<pgRoutingLayer Manual>
<Copyright(c) pgRouting Contributors>
<This documentation is licensed under a Creative Commons Attribution-Share>
<Alike 3.0 License: http://creativecommons.org/licenses/by-sa/3.0/>

# pgr_KSP
![pgr_KSP](../img/functions/f_pgr_KSP.png)

|Button|Action|
| ----------- | --------- |
|![Help](../img/functions/helpButton.png)|Opens the web page of the documentation of pgr_KSP|
|![Function](../img/functions/KSP.png)| Choose pgr_KSP on the drop down box|

## Edges SQL tab
![Edges SQL tab](../img/tabs/edges_SQL/dijkstra-KSP_edgesSQL.png)

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

## Arguments tab
![Arguments tab](../img/tabs/arguments/arguments_KSP.png)

|Field|Action|
| ----------- | --------- |
|![fromVid](../img/fields/arguments/KSP_fromVid.png)| Choose with ![plus](../img/tabs/arguments/plus_button.png) or write the comma separated identifiers of the start vertex|
|![toVid](../img/fields/arguments/KSP_toVid.png)|Choose with ![plus](../img/tabs/arguments/plus_button.png) or write the comma separated identifiers of the start vertex|
|![K](../img/fields/arguments/KSP_k.png)| ... |
|![Heap paths](../img/fields/arguments/KSP_heapPaths.png)| Tick.. ![Heap paths](../img/fields/arguments/KSP_heapPathsON.png)
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
(<U|D>) pgr_KSP: <source_id>  to <target_id>  BBOX(<bbox>)
(M <U|D>) pgr_KSP: <source_id>  to <target_id>  BBOX(<bbox>)
```