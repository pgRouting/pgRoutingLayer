# pgr_drivingDistance

- Uses BBOX of the QGIS canvas to limit the resulting path(s)

- Buttons:
  - ![Preview](../img/preview.png): Draws in the canvas the resulting path
  - ![Clear Preview](../img/clearpreview.png): Removes from the canvas objects generated with Preview
  - ![Export](../img/export.png): Creates a one row per edge line geometry layer
  	- Layer name:
	```
	(< U|D >) pgr_drivingDistance: < source_id >  to < target_id>  BBOX(< bbox >)
	```
  - ![Export Merged](../img/exportmerged.png): Creates a one row per path multiline geometry layer. As many rows as needed.
	- Layer name:
	```
	(M < U|D >) pgr_drivingDistance: < source_id >  to < target_id>  BBOX(< bbox >)
	```

## TODO fix image
![pgr_astar01](../img/pgr_astar01.png)