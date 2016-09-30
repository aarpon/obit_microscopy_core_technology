obit_microscopy_core_technology
===============================

openBIS microscopy core technology requires `openBIS 16.05.0` or newer, but version `16.05.2` is recommended. To enable the microscopy core technology in `openBIS 16.05.2` , add the following line to `openbis/servers/core-plugins/core-plugins.properties`:

```bash
enabled-modules = microscopy
```

If you are still running `openBIS 16.05.0`, you will need to use the following configuration instead (some issues with dependences on the screening core technology were addressed in the `15.06.1` patch release): 

```bash
enabled-modules = screening, microscopy
disabled-core-plugins = screening:dropboxes, screening:initialize-master-data, screening:image-overview-plugins, screening:maintenance-tasks, screening:reporting-plugins, microscopy:data-sources, microscopy:services
```
