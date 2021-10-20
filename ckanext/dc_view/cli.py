import ckan.model as model

import click


from . import jobs


def click_echo(message, am_on_a_new_line):
    if not am_on_a_new_line:
        click.echo("")
    click.echo(message)


@click.option('--force', help="Regenerate preview for all resources",
              is_flag=True)
@click.command()
def run_jobs_dc_view(force=False):
    """Generate preview image for all RT-DC resources

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
            try:
                if jobs.create_preview_job(res_dict, override=force):
                    click_echo(f"Created preview for {resource.name}", nl)
                    nl = True
            except KeyboardInterrupt:
                raise
            except BaseException as e:
                click_echo(
                    f"{e.__class__.__name__}: {e} for {res_dict['name']}", nl)
                nl = True
    if not nl:
        click.echo("")
    click.echo("Done!")


def get_commands():
    return [run_jobs_dc_view]
