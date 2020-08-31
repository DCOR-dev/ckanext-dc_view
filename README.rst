ckanext-dc_view
===============

A CKAN resource view for DC data. The preview includes metadata from
the HDF5 attributes and a summary plot (scatter plot of brightness vs. area
and image, contour, mask, and fluorescence data for one event). This plugin
registers a background job for generating the overview plot after a DC
resource has been created.

This extensione implements:

- A default view for RT-DC (mimetype) resources
- A background job that generates the preview image
- A route that makes the preview image available via
  "/dataset/{id}/resource/{resource_id}/preview.jpg"


Installation
------------

::

    pip install ckanext-dc_view


Add this extension to the plugins and defaul_views in ckan.ini:
```
ckan.plugins = [...] dc_view
ckan.views.default_views = [...] dc_view
```
