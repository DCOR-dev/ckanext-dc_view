import cgi
import pathlib

import ckan.tests.helpers as helpers


data_path = pathlib.Path(__file__).parent / "data"


def make_dataset(create_context, owner_org, with_resource=False,
                 activate=False, **kwargs):
    if "title" not in kwargs:
        kwargs["title"] = "test-dataset"
    if "authors" not in kwargs:
        kwargs["authors"] = "Peter Pan"
    if "license_id" not in kwargs:
        kwargs["license_id"] = "CC-BY-4.0"
    assert "state" not in kwargs, "must not be set"
    assert "owner_org" not in kwargs, "must not be set"
    # create a dataset
    ds = helpers.call_action("package_create", create_context,
                             owner_org=owner_org["name"],
                             state="draft",
                             **kwargs
                             )
    if with_resource:
        rs = make_resource(create_context, dataset_id=ds["id"])

    if activate:
        helpers.call_action("package_patch", create_context,
                            id=ds["id"],
                            state="active")

    dataset = helpers.call_action("package_show", id=ds["id"])

    if with_resource:
        resource = helpers.call_action("resource_show", id=rs["id"])
        return dataset, resource
    else:
        return dataset


def make_resource(create_context, dataset_id):
    path = data_path / "calibration_beads_47.rtdc"
    with path.open('rb') as fd:
        upload = cgi.FieldStorage()
        upload.filename = path.name
        upload.file = fd
        res = helpers.call_action("resource_create", create_context,
                                  package_id=dataset_id,
                                  upload=upload,
                                  url="upload",
                                  name=path.name,
                                  )
    return res
