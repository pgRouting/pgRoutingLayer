## The Buttons
There are 4 buttons for controlling how to render the pgRouting query:

![buttons](../img/buttons.png)


### Preview
Draws in the canvas the resulting path.

Creates a temporary lines on the canvas. No additional information is shown, except for pgr_dijkstraCost where an annotation is also created.


### Clear Preview
Removes from the canvas objects generated with Preview

When Clear Preview is called the generated temporary lines and annotation are deleted from the canvas. When the QGIS project is saved when there are visible annotations:

- Those annotations will be saved as part of the project
- Can be cleared with Clear Preview button, but the project needs to be saved again. On reopening a project that has annotation:
- The annotations will be shown, but won't be cleared using the Clear Preview button, they are not under the pgRoutingLayer GUI control


### Export
Creates a one row per edge line geometry layer


### Export Merged
Creates a one row per path multi-line geometry layer.

Only one row is generated. Not all functions results can be merged, when that is the case then the button is dimmed.
