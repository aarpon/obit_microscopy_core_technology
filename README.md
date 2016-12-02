# openBIS Importer Toolset :: Microscopy Core Technology

The openBIS Importer toolset is a tightly integrated collection of tools that allows for the semi-automated, semi-unsupervised registration of annotated datasets into openBIS directly from the acquisition stations; but it also extends openBIS itself with custom data viewers and server-side core plug-ins packaged into two new core technologies for **flow cytometry** and **microscopy**.

openBIS microscopy core technology requires `openBIS 16.05.0` or newer, but version `16.05.2` is recommended. To enable the microscopy core technology in `openBIS 16.05.2` , add the following line to `openbis/servers/core-plugins/core-plugins.properties`:

```bash
enabled-modules = microscopy
```

If you are still running `openBIS 16.05.{0|1}`, you will need to use the following configuration instead (some issues with dependences on the screening core technology were addressed in the `15.06.2` patch release): 

```bash
enabled-modules = screening, microscopy
disabled-core-plugins = screening:dropboxes, screening:initialize-master-data, screening:image-overview-plugins, screening:maintenance-tasks, screening:reporting-plugins, microscopy:data-sources, microscopy:services
```
## User manuals and administration guides

oBIT website: https://wiki-bsse.ethz.ch/display/oBIT
