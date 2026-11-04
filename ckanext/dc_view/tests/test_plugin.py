"""Tests for plugin.py."""
import pytest

import ckanext.dc_view.plugin as plugin  # noqa: F401


def test_plugin_info():
    p = plugin.DCViewPlugin()
    info = p.info()
    assert info["name"] == "dc_view"


@pytest.mark.ckan_config("ckan.site_url", "http://test.ckan.net")
@pytest.mark.usefixtures("ckan_config")
def test_plugin_can_view():
    p = plugin.DCViewPlugin()
    res = {"mimetype": "RT-DC",
           "url": "http://test.ckan.net/dataset/a/resource/b/download/c"}
    assert p.can_view({"resource": res})
    res["mimetype"] = "text/plain"
    assert not p.can_view({"resource": res})


def test_plugin_get_commands():
    p = plugin.DCViewPlugin()
    names = [c.name for c in p.get_commands()]
    assert "run-jobs-dc-view" in names


def test_plugin_template_variables():
    p = plugin.DCViewPlugin()
    data_dict = {"package": {"id": "ds-id"},
                 "resource": {"id": "res-id",
                              "dc:experiment:sample": "beads"}}
    variables = p.setup_template_variables({}, data_dict)
    assert variables["preview_url"] == \
        "/dataset/ds-id/resource/res-id/preview.jpg"
    assert "beads" in variables["metadata_html"]
    assert p.view_template({}, data_dict) == "dc_view.html"
