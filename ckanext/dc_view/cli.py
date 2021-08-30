import ckan.model as model

import click


from . import jobs


@click.command()
def run_jobs_dc_view():
    """Compute preview image for all .rtdc files

    This also happens for draft datasets.
    """
    # go through all datasets
    datasets = model.Session.query(model.Package)
    nl = False  # new line character
    for dataset in datasets:
        nl = False
        click.echo(f"Checking dataset {dataset.id}\r", nl=False)
        for resource in dataset.resources:
            res_dict = resource.as_dict()
            if jobs.create_preview_job(res_dict, override=False):
                click.echo("")
                nl = True
                click.echo(f"Created preview for {resource.name}")
    if not nl:
        click.echo("")
    click.echo("Done!")


def get_commands():
    return [run_jobs_dc_view]
