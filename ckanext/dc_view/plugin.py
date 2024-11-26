from flask import Blueprint
import ckan.lib.datapreview as datapreview
import ckan.plugins as plugins

from dcor_shared import DC_MIME_TYPES, s3

from .cli import get_commands
from . import jobs
from .meta import render_metadata_html
from .route_funcs import dcpreview


class DCViewPlugin(plugins.SingletonPlugin):
    """DC data view and route for *_preview.png"""
    plugins.implements(plugins.IBlueprint, inherit=True)
    plugins.implements(plugins.IClick, inherit=True)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.IResourceView, inherit=True)

    # IBlueprint
    def get_blueprint(self):
        """"Return a Flask Blueprint object to be registered by the app."""

        # Create Blueprint for plugin
        blueprint = Blueprint(self.name, self.__module__)

        # Add plugin url rules to Blueprint object
        rules = [
            ('/dataset/<uuid:ds_id>/resource/<uuid:res_id>/preview.jpg',
             'dcpreview',
             dcpreview),
        ]
        for rule in rules:
            blueprint.add_url_rule(*rule)
        return blueprint

    # IClick
    def get_commands(self):
        return get_commands()

    # IConfigurer
    def update_config(self, config):
        plugins.toolkit.add_template_directory(config, 'templates')
        plugins.toolkit.add_resource('assets', 'dc_view')

    # IResourceController
    def after_resource_create(self, context, resource):
        """Generate preview image and upload to S3"""
        # We only create the preview and upload it to S3 if the file is
        # a DC file and if S3 is available.
        if not context.get("is_background_job") and s3.is_available():
            # All jobs are defined via decorators in jobs.py
            jobs.RQJob.enqueue_all_jobs(resource, ckanext="dc_view")

    # IResourceView
    def info(self):
        return {'name': 'dc_view',
                'title': plugins.toolkit._('DC Info'),
                'icon': 'microscope',
                'iframed': False,
                'always_available': True,
                'default_title': plugins.toolkit._('DC Info'),
                }

    def can_view(self, data_dict):
        resource = data_dict['resource']
        mtype = resource.get('mimetype', '')
        same_domain = datapreview.on_same_domain(data_dict)
        if mtype in DC_MIME_TYPES and same_domain:
            return True
        else:
            return False

    def setup_template_variables(self, context, data_dict):
        ds_id = data_dict["package"]["id"]
        rid = data_dict["resource"]["id"]
        preview_url = f"/dataset/{ds_id}/resource/{rid}/preview.jpg"
        metadata_html = render_metadata_html(data_dict["resource"])
        return {
            'metadata_html': metadata_html,
            'preview_url': preview_url,
        }

    def view_template(self, context, data_dict):
        return 'dc_view.html'
