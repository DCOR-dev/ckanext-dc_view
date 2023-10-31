import pathlib

import flask
from ckan.common import c
import ckan.lib.uploader as uploader
from ckan import logic
import ckan.model as model
import ckan.plugins.toolkit as toolkit

import botocore.exceptions
from dcor_shared import get_ckan_config_option, s3


def dcpreview(ds_id, res_id):
    """Serve a preview image on disk

    Parameters
    ----------
    ds_id: str
        dataset ID
    res_id: str
        resource ID for which to return the preview image
    """
    # Code borrowed from ckan/controllers/package.py:resource_download
    context = {'model': model, 'session': model.Session,
               'user': c.user, 'auth_user_obj': c.userobj}
    did = str(ds_id)
    rid = str(res_id)
    try:
        res_dict = toolkit.get_action('resource_show')(context, {'id': rid})
        ds_dict = toolkit.get_action('package_show')(context, {'id': did})
    except (logic.NotFound, logic.NotAuthorized):
        # Treat not found and not authorized equally, to not leak information
        # to unprivileged users.
        return toolkit.abort(404, toolkit._('Resource not found'))

    res_stem, _ = res_dict["name"].rsplit(".", 1)
    prev_name = f"{res_stem}_preview.jpg"

    if s3 is not None and res_dict.get('s3_available'):
        # check if the corresponding S3 object exists
        bucket_name = get_ckan_config_option(
            "dcor_object_store.bucket_name").format(
            organization_id=ds_dict["organization"]["id"])
        object_name = f"preview/{rid[:3]}/{rid[3:6]}/{rid[6:]}"
        s3_client, _, _ = s3.get_s3()
        try:
            s3_client.head_object(Bucket=bucket_name,
                                  Key=object_name)
        except botocore.exceptions.ClientError:
            pass
        else:
            # We have an S3 object that we can redirect to. We are making use
            # of presigned URLs to be able to specify a filename for download
            # (otherwise, users that download via the web interface will
            # just get a hash as a file name without any suffix or human-
            # readable identifier).
            if ds_dict["private"]:
                expiration = 3600
            else:
                expiration = 86400
            ps_url = s3.create_presigned_url(
                bucket_name=bucket_name,
                object_name=object_name,
                filename=prev_name,
                expiration=expiration)
            return toolkit.redirect_to(ps_url)

    if res_dict.get('url_type') == 'upload':
        upload = uploader.get_resource_uploader(res_dict)
        filepath = pathlib.Path(upload.get_path(res_dict['id']))
        jpg_file = filepath.with_name(filepath.name + "_preview.jpg")
        if not jpg_file.exists():
            return toolkit.abort(404, toolkit._('Preview not found'))
        return flask.send_from_directory(jpg_file.parent, jpg_file.name,
                                         attachment_filename=prev_name)
    return toolkit.abort(404, toolkit._('No preview available'))
