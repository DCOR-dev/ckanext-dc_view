from unittest import mock

import ckan.common
import ckan.model
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
import ckanext.dcor_schemas.plugin
import dcor_shared

import pytest

from .helper_methods import make_dataset, synchronous_enqueue_job


@pytest.mark.ckan_config('ckan.plugins',
                         'dcor_depot dcor_schemas dc_serve dc_view')
@pytest.mark.usefixtures('clean_db', 'with_request_context')
@mock.patch('ckan.plugins.toolkit.enqueue_job',
            side_effect=synchronous_enqueue_job)
def test_route_redircet_preview_to_s3_private(
        enqueue_job_mock, app, tmpdir, create_with_upload, monkeypatch,
        ckan_config):
    monkeypatch.setitem(ckan_config, 'ckan.storage_path', str(tmpdir))
    monkeypatch.setattr(ckan.lib.uploader,
                        'get_storage_path',
                        lambda: str(tmpdir))
    monkeypatch.setattr(
        ckanext.dcor_schemas.plugin,
        'DISABLE_AFTER_DATASET_CREATE_FOR_CONCURRENT_JOB_TESTS',
        True)

    user = factories.User()
    user_obj = ckan.model.User.by_name(user["name"])
    monkeypatch.setattr(ckan.common,
                        'current_user',
                        user_obj)
    owner_org = factories.Organization(users=[{
        'name': user['id'],
        'capacity': 'admin'
    }])
    # Note: `call_action` bypasses authorization!
    create_context = {'ignore_auth': False,
                      'user': user['name'],
                      'api_version': 3}
    # create a dataset
    ds_dict, res_dict = make_dataset(create_context, owner_org,
                                     create_with_upload=create_with_upload,
                                     activate=True,
                                     private=True
                                     )
    rid = res_dict["id"]
    assert "s3_available" in res_dict
    assert "s3_url" in res_dict

    # Remove the local resource to make sure CKAN serves the S3 URL
    path = dcor_shared.get_resource_path(rid)
    path_prev = path.with_name(path.name + "_preview.jpg")
    assert path_prev.exists()
    path_prev.unlink()

    did = ds_dict["id"]
    # We should not be authorized to access the resource without API token
    resp0 = app.get(
        f"/dataset/{did}/resource/{rid}/preview.jpg",
        status=404
        )
    assert len(resp0.history) == 0

    # Try again with token
    data = helpers.call_action(
        u"api_token_create",
        context={u"model": ckan.model, u"user": user[u"name"]},
        user=user[u"name"],
        name=u"token-name",
    )

    resp = app.get(
        f"/dataset/{did}/resource/{rid}/preview.jpg",
        headers={u"authorization": data["token"]},
        )

    endpoint = dcor_shared.get_ckan_config_option(
        "dcor_object_store.endpoint_url")
    bucket_name = dcor_shared.get_ckan_config_option(
        "dcor_object_store.bucket_name").format(
        organization_id=ds_dict["organization"]["id"])
    redirect = resp.history[0]
    assert redirect.status_code == 302
    redirect_stem = (f"{endpoint}/{bucket_name}/preview/"
                     f"{rid[:3]}/{rid[3:6]}/{rid[6:]}")
    # Since we have a presigned URL, it is longer than the normal S3 URL.
    assert redirect.location.startswith(redirect_stem)
    assert len(redirect.location) > len(redirect_stem)


@pytest.mark.ckan_config('ckan.plugins',
                         'dcor_depot dcor_schemas dc_serve dc_view')
@pytest.mark.usefixtures('clean_db', 'with_request_context')
@mock.patch('ckan.plugins.toolkit.enqueue_job',
            side_effect=synchronous_enqueue_job)
def test_route_preview_to_s3_public(
        enqueue_job_mock, app, tmpdir, create_with_upload, monkeypatch,
        ckan_config):
    monkeypatch.setitem(ckan_config, 'ckan.storage_path', str(tmpdir))
    monkeypatch.setattr(ckan.lib.uploader,
                        'get_storage_path',
                        lambda: str(tmpdir))
    monkeypatch.setattr(
        ckanext.dcor_schemas.plugin,
        'DISABLE_AFTER_DATASET_CREATE_FOR_CONCURRENT_JOB_TESTS',
        True)

    user = factories.User()
    user_obj = ckan.model.User.by_name(user["name"])
    monkeypatch.setattr(ckan.common,
                        'current_user',
                        user_obj)
    owner_org = factories.Organization(users=[{
        'name': user['id'],
        'capacity': 'admin'
    }])
    # Note: `call_action` bypasses authorization!
    create_context = {'ignore_auth': False,
                      'user': user['name'],
                      'api_version': 3}
    # create a dataset
    ds_dict, res_dict = make_dataset(create_context, owner_org,
                                     create_with_upload=create_with_upload,
                                     activate=True)
    rid = res_dict["id"]
    assert "s3_available" in res_dict
    assert "s3_url" in res_dict

    # Remove the local resource to make sure CKAN serves the S3 URL
    path = dcor_shared.get_resource_path(rid)
    path_prev = path.with_name(path.name + "_preview.jpg")
    assert path_prev.exists()
    path_prev.unlink()

    did = ds_dict["id"]
    resp = app.get(
        f"/dataset/{did}/resource/{rid}/preview.jpg",
        )

    endpoint = dcor_shared.get_ckan_config_option(
        "dcor_object_store.endpoint_url")
    bucket_name = dcor_shared.get_ckan_config_option(
        "dcor_object_store.bucket_name").format(
        organization_id=ds_dict["organization"]["id"])
    redirect = resp.history[0]
    assert redirect.status_code == 302
    assert redirect.location.startswith(f"{endpoint}/{bucket_name}/preview/"
                                        f"{rid[:3]}/{rid[3:6]}/{rid[6:]}")
