obit_microscopy_core_technology
===============================

openBIS microscopy core technology.

The microscopy core technology still depends on some functionalities provided by the screening core technology. To enable, add these lines to `openbis/servers/core-plugins/core-plugins.properties`.

```bash
enabled-modules = screening, microscopy
disabled-core-plugins = screening:dropboxes, screening:initialize-master-data, screening:image-overview-plugins, screening:maintenance-tasks, screening:reporting-plugins, microscopy:data-sources, microscopy:services
````
