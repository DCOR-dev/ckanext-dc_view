import numbers

import dclab


def render_metadata_html(res_dict):
    # build dictionary from metadata
    meta = {}
    for dckey in res_dict:
        if dckey.startswith("dc:"):
            _, sec, key = dckey.split(":")
            if sec not in meta:
                meta[sec] = {}
            meta[sec][key] = res_dict[dckey]

    html = []
    for sec in ["experiment", "setup", "imaging", "fluorescence"]:
        if sec in meta:
            html += meta_html_table(meta, sec)
            html.append("<br>")

    return "\n".join(html)


def meta_html_table(meta, sec):
    html = [
        '<table class="table table-striped table-bordered table-condensed">',
        "<caption>{}</caption>".format(sec.capitalize()),
    ]

    kn = [(dclab.dfn.config_descr[sec][key], key) for key in meta[sec].keys()]
    for name, key in sorted(kn):
        value = meta[sec][key]
        if isinstance(value, numbers.Number):
            value = "{:.4g}".format(value)

        # Special cases
        if sec == "experiment":
            if key in ["date", "time"]:
                name, _ = name.split("(")
            elif key == "sample":
                name = "Sample name"
        elif sec == "setup":
            if key == "chip region":
                name = name.split(" (")[0]
            elif key == "medium" and value == "CellCarrierB":
                value = "CellCarrier B"
            elif key == "module composition":
                name = "Modules used"
                value = ", ".join(value.split(","))
            elif key == "software version":
                name = "Software"

        # Units
        if name.endswith("]"):
            name, units = name.rsplit(" [", 1)
            units = units.strip("] ")
            value += " " + units

        html += [
            '<tr>',
            u'<th class="dataset-labels">{}</th>'.format(name),
            u'<td class="dataset-details">{}</td>'.format(value),
            '</tr>',
        ]
    html.append("</table>")
    return html
