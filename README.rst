ckanext-dc_view
===============

A CKAN resource view for DC data. The preview includes metadata from
the HDF5 attributes and a summary plot (scatter plot of brightness vs. area
and image, contour, mask, and fluorescence data for one event). This plugin
registers a background job for generating the overview plot after a DC
resource has been created.


Installation
------------

::

    pip install ckanext-dc_view


Add this extension to the plugins and defaul_views in ckan.ini:
```
ckan.plugins = [...] dc_view
ckan.views.default_views = [...] dc_view
```
