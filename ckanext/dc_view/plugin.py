from flask import Blueprint
from ckan.common import config
import ckan.lib.datapreview as datapreview
import ckan.plugins.toolkit as toolkit
import ckan.plugins as plugins

from dcor_shared import DC_MIME_TYPES

from .cli import get_commands
from .jobs import create_preview_job
from .meta import render_metadata_html
from .route_funcs import dcpreview


class DCViewPlugin(plugins.SingletonPlugin):
    """DC data view and route for *_preview.png"""
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IClick)
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
            ('/dataset/<uuid:id>/resource/<uuid:resource_id>/preview.jpg',
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
    def after_create(self, context, resource):
        """Generate preview data"""
        if resource.get('mimetype') in DC_MIME_TYPES:
            pkg_job_id = f"{resource['package_id']}_{resource['position']}_"
            jid_preview = pkg_job_id + "preview"
            jid_condense = pkg_job_id + "condense"
            exts = config.get("ckan.plugins")
            if "dc_serve" in exts:
                # The dc_serve extension is available, which produces a
                # condensed dataset. We can use that for plotting.
                rq_kwargs = {"timeout": 60,
                             "job_id": jid_preview,
                             "depends_on": jid_condense}
                queue = "dcor-normal"
            else:
                # The dc_serve extension is NOT available. Creating the preview
                # image might take longer.
                rq_kwargs = {"timeout": 1800,
                             "job_id": jid_preview}
                queue = "dcor-long"
            toolkit.enqueue_job(create_preview_job,
                                [resource],
                                title="Create resource preview image",
                                queue=queue,
                                rq_kwargs=rq_kwargs)

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
        preview_url = '/dataset/{}/resource/{}/preview.jpg'.format(
            data_dict['package']['id'], data_dict['resource']['id'])
        metadata_html = render_metadata_html(data_dict["resource"])
        return {
            'metadata_html': metadata_html,
            'preview_url': preview_url,
        }

    def view_template(self, context, data_dict):
        return 'dc_view.html'
