ckanext-dc_view
===============

|PyPI Version| |Build Status| |Coverage Status|

A CKAN resource view for DC data. The preview includes metadata from
the HDF5 attributes and a summary plot (scatter plot of brightness vs. area
and image, contour, mask, and fluorescence data for one event). This plugin
registers a background job for generating the overview plot after a DC
resource has been created.

This extensione implements:

- A default view for DC (mimetype) resources
- A background job that generates the preview image
- A background job that uploads preview images to the S3 object store
- A route that makes the preview image available via
  "/dataset/{id}/resource/{resource_id}/preview.jpg"


- CLI:

  - add CKAN command `run-jobs-dc-view` that runs all background
    jobs for all resources (if not already done)

Installation
------------

::

    pip install ckanext-dc_view


Add this extension to the plugins and defaul_views in ckan.ini:

::

    ckan.plugins = [...] dc_view
    ckan.views.default_views = [...] dc_view


Testing
-------
Testing is implemented via GitHub Actions. You may also set up a local
docker container with CKAN and MinIO. Take a look at the GitHub Actions
workflow for more information.


.. |PyPI Version| image:: https://img.shields.io/pypi/v/ckanext.dc_view.svg
   :target: https://pypi.python.org/pypi/ckanext.dc_view
.. |Build Status| image:: https://img.shields.io/github/actions/workflow/status/DCOR-dev/ckanext-dc_view/check.yml
   :target: https://github.com/DCOR-dev/ckanext-dc_view/actions?query=workflow%3AChecks
.. |Coverage Status| image:: https://img.shields.io/codecov/c/github/DCOR-dev/ckanext-dc_view
   :target: https://codecov.io/gh/DCOR-dev/ckanext-dc_view
