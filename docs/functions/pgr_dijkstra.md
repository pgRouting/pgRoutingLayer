# pgr_dijkstra

- Uses BBOX of the QGIS canvas to limit the resulting path(s)

- Buttons:
  - Preview: Draws in the canvas the resulting path
  - Clear Preview: Removes from the canvas objects generated with Preview
  - Export: Creates a one row per edge line geometry layer
  - Export Merged: Creates a one row per path multiline geometry layer. As many rows as needed.
- Layer name:
```
(< M >< U|D >) dijkstra: < source_ids > to < target_ids> BBOX(< bbox >)
```

![pgr_dijkstra01](../img/pgr_dijkstra01.png)
