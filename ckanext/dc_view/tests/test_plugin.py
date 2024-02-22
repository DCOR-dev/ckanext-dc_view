"""Tests for plugin.py."""
import ckanext.dc_view.plugin as plugin  # noqa: F401


def test_plugin_info():
    p = plugin.DCViewPlugin()
    info = p.info()
    assert info["name"] == "dc_view"
