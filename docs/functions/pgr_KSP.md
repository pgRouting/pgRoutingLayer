# pgr_KSP

- Uses BBOX of the QGIS canvas to limit the resulting path(s)

- Buttons:
  - ![Preview](../img/buttons/execute/preview.png): Draws in the canvas the resulting path
  - ![Clear Preview](../img/buttons/execute/clearpreview.png): Removes from the canvas objects generated with Preview
  - ![Export](../img/buttons/execute/export.png): Creates a one row per edge line geometry layer
  	- Layer name:
	```
	(< U|D >) pgr_KSP: < source_id >  to < target_id>  BBOX(< bbox >)
	```
   - ![Export Merged](../img/buttons/execute/exportmergedON.png): Creates a one row per path multiline geometry layer. As many rows as needed.
	- Layer name:
	```
	(M < U|D >) pgr_KSP: < source_id >  to < target_id>  BBOX(< bbox >)
	```

![pgr_astar01](../img/tabs/execute/execute.png)
