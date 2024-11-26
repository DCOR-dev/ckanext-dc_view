import html
import numbers

import dclab
from dclab.features.emodulus.viscosity import ALIAS_MEDIA


def render_metadata_html(res_dict):
    # build dictionary from metadata
    meta = {}
    for dckey in res_dict:
        if dckey.startswith("dc:"):
            _, sec, key = dckey.split(":")
            if sec not in meta:
                meta[sec] = {}
            meta[sec][key] = res_dict[dckey]

    html_code = []
    for sec in ["experiment", "pipeline", "setup", "imaging", "fluorescence"]:
        if sec in meta:
            html_code += meta_html_table(meta, sec)
            html_code.append("<br>")

    return "\n".join(html_code)


def meta_html_table(meta, sec):
    html_code = [
        '<table class="table table-striped '
        + 'table-bordered table-condensed dc_view">',
        f'<caption class="dc_view">{sec.capitalize()}</caption>',
    ]

    kn = [(dclab.dfn.config_descr[sec][key], key) for key in meta[sec].keys()]
    for name, key in sorted(kn):
        value = meta[sec][key]
        if isinstance(value, numbers.Number):
            value = f"{value:.4g}"

        # Special cases
        if sec == "experiment":
            if key in ["date", "time"]:
                name, _ = name.split("(")
            elif key == "sample":
                name = "Sample name"
        elif sec == "setup":
            if key == "chip region":
                name = name.split(" (")[0]
            elif key == "medium" and value in ALIAS_MEDIA:
                # Convert names to common names
                value = ALIAS_MEDIA[value]
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

        html_code += [
            '<tr>',
            f'<th class="dataset-labels">{html.escape(name)}</th>',
            f'<td class="dataset-details">{html.escape(value)}</td>',
            '</tr>',
        ]
    html_code.append("</table>")
    return html_code
