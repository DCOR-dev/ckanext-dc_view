import pathlib
from unittest import mock

from dcor_shared.testing import make_dataset_via_s3, synchronous_enqueue_job

import pytest

from ckanext.dc_view.cli import run_jobs_dc_view


data_path = pathlib.Path(__file__).parent / "data"


@pytest.mark.ckan_config('ckan.plugins', 'dcor_schemas dc_view')
@pytest.mark.usefixtures('clean_db', 'with_request_context')
@mock.patch('ckan.plugins.toolkit.enqueue_job',
            side_effect=synchronous_enqueue_job)
def test_cli_run_jobs_dc_view(enqueue_job_mock, cli):
    make_dataset_via_s3(
        resource_path=data_path / "calibration_beads_47.rtdc",
        activate=True)
    result = cli.invoke(run_jobs_dc_view,
                        ["--modified-days", "1", "--force"])
    assert result.exit_code == 0
    assert "Checking dataset" in result.output
    assert "OK: " in result.output
    assert "Done!" in result.output
