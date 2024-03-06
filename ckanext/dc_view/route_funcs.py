from ckan.common import c
from ckan import logic
import ckan.model as model
import ckan.plugins.toolkit as toolkit

from dcor_shared import s3, s3cc


def dcpreview(ds_id, res_id):
    """Redirect to a preview image on S3 for a DC resource

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

    res_stem = res_dict["name"].rsplit(".", 1)[0]
    prev_name = f"{res_stem}_preview.jpg"

    if s3.is_available() and res_dict.get('s3_available'):
        # check if the corresponding S3 object exists
        if s3cc.artifact_exists(resource_id=rid, artifact="preview"):
            # We have an S3 object that we can redirect to. We are making use
            # of presigned URLs to be able to specify a filename for download
            # (otherwise, users that download via the web interface will
            # just get a hash as a file name without any suffix or human-
            # readable identifier).
            if ds_dict["private"]:
                expiration = 3600
            else:
                expiration = 86400
            bucket_name, object_name = s3cc.get_s3_bucket_object_for_artifact(
                resource_id=rid, artifact="preview")
            ps_url = s3.create_presigned_url(
                bucket_name=bucket_name,
                object_name=object_name,
                filename=prev_name,
                expiration=expiration)
            return toolkit.redirect_to(ps_url)

    return toolkit.abort(404, toolkit._('No preview available'))
