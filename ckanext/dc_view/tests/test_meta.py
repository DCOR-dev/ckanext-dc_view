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


def test_render_metadata_html_special_cases():
    html = render_metadata_html({
        "dc:experiment:date": "2016-03-02",
        "dc:experiment:time": "12:34:56",
        "dc:experiment:sample": "beads",
        "dc:setup:chip region": "channel",
        "dc:setup:medium": "0.5% MC-PBS",
        "dc:setup:module composition": "Cell_Flow_2,Fluor",
        "dc:setup:software version": "ShapeIn 2.0.1",
        "dc:setup:flow rate": 0.04,
    })
    assert "Sample name" in html
    assert "Imaged chip region" in html
    assert "(channel or reservoir)" not in html
    # medium alias is converted to its common name
    assert "0.49% MC-PBS" in html
    assert "Modules used" in html
    assert "Cell_Flow_2, Fluor" in html
    assert "Software" in html
    # units are appended to the value
    assert "0.04 µL/s" in html
