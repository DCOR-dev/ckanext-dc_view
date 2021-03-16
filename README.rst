ckanext-dc_view
===============

|PyPI Version| |Build Status| |Coverage Status|

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

::

    ckan.plugins = [...] dc_view
    ckan.views.default_views = [...] dc_view


Testing
-------
If CKAN/DCOR is installed and setup for testing, this extension can
be tested with pytest:

::

    pytest ckanext

Testing can also be done via vagrant in a virtualmachine using the
`dcor-test <https://app.vagrantup.com/paulmueller/boxes/dcor-test/>` image.
Make sure that `vagrant` and `virtualbox` are installed and run the
following commands in the root of this repository:

::

    # Setup virtual machine using `Vagrantfile`
    vagrant up
    # Run the tests
    vagrant ssh -- sudo bash /testing/vagrant-run-tests.sh


.. |PyPI Version| image:: https://img.shields.io/pypi/v/ckanext.dc_view.svg
   :target: https://pypi.python.org/pypi/ckanext.dc_view
.. |Build Status| image:: https://img.shields.io/github/workflow/status/DCOR-dev/ckanext-dc_view/Checks
   :target: https://github.com/DCOR-dev/ckanext-dc_view/actions?query=workflow%3AChecks
.. |Coverage Status| image:: https://img.shields.io/codecov/c/github/DCOR-dev/ckanext-dc_view
   :target: https://codecov.io/gh/DCOR-dev/ckanext-dc_view
