import pathlib
from unittest import mock

import ckan.common
import ckan.model
import ckan.tests.factories as factories
import dcor_shared
from dcor_shared.testing import (  # noqa: F401
    make_dataset_via_s3, synchronous_enqueue_job,
    create_with_upload_no_temp
)

import pytest


data_path = pathlib.Path(__file__).parent / "data"


@pytest.mark.ckan_config('ckan.plugins', 'dcor_schemas dc_serve dc_view')
@pytest.mark.usefixtures('clean_db')
@mock.patch('ckan.plugins.toolkit.enqueue_job',
            side_effect=synchronous_enqueue_job)
def test_route_s3_redirect_preview_to_s3_private(
        enqueue_job_mock, app, monkeypatch):
    user = factories.UserWithToken()
    user_obj = ckan.model.User.by_name(user["name"])
    monkeypatch.setattr(ckan.common,
                        'current_user',
                        user_obj)

    # Note: `call_action` bypasses authorization!
    create_context = {'ignore_auth': False,
                      'user': user['name'],
                      'api_version': 3}
    # create a dataset
    ds_dict, res_dict = make_dataset_via_s3(
        create_context=create_context,
        resource_path=data_path / "calibration_beads_47.rtdc",
        activate=True,
        private=True
        )
    rid = res_dict["id"]
    assert "s3_available" in res_dict
    assert "s3_url" in res_dict
    assert len(res_dict.get("url"))

    did = ds_dict["id"]
    # We should not be authorized to access the resource without API token
    resp0 = app.get(
        f"/dataset/{did}/resource/{rid}/preview.jpg",
        status=404,
        follow_redirects=False,
        )
    assert len(resp0.history) == 0

    # Try again with token
    resp = app.get(
        f"/dataset/{did}/resource/{rid}/preview.jpg",
        headers={"Authorization": user["token"]},
        follow_redirects=False,
        )

    endpoint = dcor_shared.get_ckan_config_option(
        "dcor_object_store.endpoint_url")
    bucket_name = dcor_shared.get_ckan_config_option(
        "dcor_object_store.bucket_name").format(
        organization_id=ds_dict["organization"]["id"])
    redirect = resp
    assert redirect.status_code == 302
    redirect_stem = (f"{endpoint}/{bucket_name}/preview/"
                     f"{rid[:3]}/{rid[3:6]}/{rid[6:]}")
    # Since we have a presigned URL, it is longer than the normal S3 URL.
    assert redirect.location.startswith(redirect_stem)
    assert len(redirect.location) > len(redirect_stem)


@pytest.mark.ckan_config('ckan.plugins', 'dcor_schemas dc_serve dc_view')
@pytest.mark.usefixtures('clean_db')
@mock.patch('ckan.plugins.toolkit.enqueue_job',
            side_effect=synchronous_enqueue_job)
def test_route_s3_redirect_preview_to_s3_public(enqueue_job_mock, app):
    # create a dataset
    ds_dict, res_dict = make_dataset_via_s3(
        resource_path=data_path / "calibration_beads_47.rtdc",
        activate=True)
    rid = res_dict["id"]
    assert "s3_available" in res_dict
    assert "s3_url" in res_dict
    assert len(res_dict.get("url"))

    did = ds_dict["id"]
    resp = app.get(
        f"/dataset/{did}/resource/{rid}/preview.jpg",
        follow_redirects=False,
        )

    endpoint = dcor_shared.get_ckan_config_option(
        "dcor_object_store.endpoint_url")
    bucket_name = dcor_shared.get_ckan_config_option(
        "dcor_object_store.bucket_name").format(
        organization_id=ds_dict["organization"]["id"])
    redirect = resp
    assert redirect.status_code == 302
    assert redirect.location.startswith(f"{endpoint}/{bucket_name}/preview/"
                                        f"{rid[:3]}/{rid[3:6]}/{rid[6:]}")
