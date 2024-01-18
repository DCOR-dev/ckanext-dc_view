"""Testing background jobs

Due to the asynchronous nature of background jobs, code that uses them needs
to be handled specially when writing tests.

A common approach is to use the mock package to replace the
ckan.plugins.toolkit.enqueue_job function with a mock that executes jobs
synchronously instead of asynchronously
"""
from unittest import mock
import pathlib
import time

import pytest
import requests

import ckan.lib
import ckan.tests.factories as factories

import ckanext.dcor_schemas.plugin
import dcor_shared

from .helper_methods import make_dataset


data_dir = pathlib.Path(__file__).parent / "data"


def synchronous_enqueue_job(job_func, args=None, kwargs=None, title=None,
                            queue=None, rq_kwargs=None):
    """
    Synchronous mock for ``ckan.plugins.toolkit.enqueue_job``.
    """
    if rq_kwargs is None:
        rq_kwargs = {}
    args = args or []
    kwargs = kwargs or {}
    job_func(*args, **kwargs)


# We need the dcor_depot extension to make sure that the symbolic-
# linking pipeline is used.
@pytest.mark.ckan_config('ckan.plugins', 'dcor_depot dcor_schemas dc_view')
@pytest.mark.usefixtures('clean_db', 'with_request_context')
@mock.patch('ckan.plugins.toolkit.enqueue_job',
            side_effect=synchronous_enqueue_job)
def test_create_preview_job(enqueue_job_mock, create_with_upload, monkeypatch,
                            ckan_config, tmpdir):
    monkeypatch.setitem(ckan_config, 'ckan.storage_path', str(tmpdir))
    monkeypatch.setattr(ckan.lib.uploader,
                        'get_storage_path',
                        lambda: str(tmpdir))
    monkeypatch.setattr(
        ckanext.dcor_schemas.plugin,
        'DISABLE_AFTER_DATASET_CREATE_FOR_CONCURRENT_JOB_TESTS',
        True)

    user = factories.User()
    owner_org = factories.Organization(users=[{
        'name': user['id'],
        'capacity': 'admin'
    }])
    # Note: `call_action` bypasses authorization!
    # create 1st dataset
    create_context = {'ignore_auth': False, 'user': user['name'],
                      'api_version': 3}
    dataset = make_dataset(create_context,
                           owner_org,
                           activate=False)
    path = data_dir / "calibration_beads_47.rtdc"
    content = path.read_bytes()
    result = create_with_upload(
        content, 'test.rtdc',
        url="upload",
        package_id=dataset["id"],
        context=create_context,
    )
    resource_path = dcor_shared.get_resource_path(result["id"])
    assert resource_path.exists()
    preview_path = resource_path.with_name(resource_path.name + "_preview.jpg")
    # give the background job a little time to complete
    for ii in range(100):
        if not preview_path.exists():
            time.sleep(0.1)
        else:
            assert preview_path.stat().st_size > 1000
            break
    else:
        raise ValueError("Preview generation timed out after 10s!")


# We need the dcor_depot extension to make sure that the symbolic-
# linking pipeline is used.
@pytest.mark.ckan_config('ckan.plugins', 'dcor_depot dc_view dcor_schemas')
@pytest.mark.usefixtures('clean_db', 'with_request_context')
@mock.patch('ckan.plugins.toolkit.enqueue_job',
            side_effect=synchronous_enqueue_job)
def test_upload_preview_dataset_to_s3_job(
        enqueue_job_mock, create_with_upload, monkeypatch, ckan_config,
        tmpdir):
    monkeypatch.setitem(ckan_config, 'ckan.storage_path', str(tmpdir))
    monkeypatch.setattr(ckan.lib.uploader,
                        'get_storage_path',
                        lambda: str(tmpdir))
    monkeypatch.setattr(
        ckanext.dcor_schemas.plugin,
        'DISABLE_AFTER_DATASET_CREATE_FOR_CONCURRENT_JOB_TESTS',
        True)

    user = factories.User()
    owner_org = factories.Organization(users=[{
        'name': user['id'],
        'capacity': 'admin'
    }])
    # Note: `call_action` bypasses authorization!
    # create 1st dataset
    create_context = {'ignore_auth': False,
                      'user': user['name'],
                      'api_version': 3}
    ds_dict, res_dict = make_dataset(create_context,
                                     owner_org,
                                     create_with_upload=create_with_upload,
                                     activate=True)
    bucket_name = dcor_shared.get_ckan_config_option(
        "dcor_object_store.bucket_name").format(
        organization_id=ds_dict["organization"]["id"])
    rid = res_dict["id"]
    object_name = f"preview/{rid[:3]}/{rid[3:6]}/{rid[6:]}"
    endpoint = dcor_shared.get_ckan_config_option(
        "dcor_object_store.endpoint_url")
    prev_url = f"{endpoint}/{bucket_name}/{object_name}"
    response = requests.get(prev_url)
    assert response.ok, "resource is public"
    assert response.status_code == 200
    # Verify SHA256sum
    path = dcor_shared.get_resource_path(res_dict["id"])
    path_prev = path.with_name(path.name + "_preview.jpg")
    dl_path = tmpdir / "prev_image.jpg"
    with dl_path.open("wb") as fd:
        fd.write(response.content)
    assert dcor_shared.sha256sum(dl_path) == dcor_shared.sha256sum(path_prev)
