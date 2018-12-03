# pgr_bdastar

- Uses BBOX of the QGIS canvas to limit the resulting path(s)

- Buttons:
  - Preview: Draws in the canvas the resulting path
  - Clear Preview: Removes from the canvas objects generated with Preview
  - Export: Creates a one row per edge line geometry layer
  - Export Merged: Creates a one row per path multiline geometry layer. As many rows as needed.
- Layer name:
```
(< M >< U|D >) bdAstar: < source_id >  to < target_id>  BBOX(< bbox >)
```

![pgr_astar01](../img/pgr_astar01.png)
