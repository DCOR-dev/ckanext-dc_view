from ckanext.dc_view.meta import render_metadata_html


def test_render_metadata_html_timestamp():
    html = render_metadata_html({
        "dc:experiment:timestamp": 1742023456.1234,
        "dc:experiment:event count": 4544,
    })
    assert "1742023456.1 s" in html
    assert "e+09" not in html
    # other numbers are still formatted with four significant digits
    assert "4544" in html
