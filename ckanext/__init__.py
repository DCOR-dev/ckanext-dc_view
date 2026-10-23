# encoding: utf-8

# this is a namespace package
# (same as in CKAN, compatible with setuptools<82 and setuptools>=82,
# which does not ship `pkg_resources` anymore)
try:
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
except ImportError:
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)
