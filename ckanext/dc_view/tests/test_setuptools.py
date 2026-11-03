import subprocess
import sys


def test_import_without_pkg_resources():
    """setuptools>=82 does not ship `pkg_resources` (e.g. CKAN 2.11.6)"""
    code = ("import sys; "
            "sys.modules['pkg_resources'] = None; "  # import raises an error
            "import ckanext.dc_view.plugin")
    subprocess.check_call([sys.executable, "-c", code])
