# pgr_dijkstra

- Uses BBOX of the QGIS canvas to limit the resulting path(s)

- Buttons:
  - ![Preview](../img/preview.png): Draws in the canvas the resulting path
  - ![Clear Preview](../img/clearpreview.png): Removes from the canvas objects generated with Preview
  - ![Export](../img/export.png): Creates a one row per edge line geometry layer
  	- Layer name:
	```
	(< U|D >) pgr_dijkstra: < source_id >  to < target_id>  BBOX(< bbox >)
	```
  - ![Export Merged](../img/exportmerged.png): Creates a one row per path multiline geometry layer. As many rows as needed.
	- Layer name:
	```
	(M < U|D >) pgr_dijkstra: < source_id >  to < target_id>  BBOX(< bbox >)
	```

![pgr_dijkstra01](../img/pgr_dijkstra01.png)
