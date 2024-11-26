import datetime
import time
import traceback

import ckan.model as model

import click


from . import jobs


def click_echo(message, am_on_a_new_line):
    if not am_on_a_new_line:
        click.echo("")
    click.echo(message)


@click.option('--modified-days', default=-1,
              help='Only run for datasets modified within this number of days '
                   + 'in the past. Set to -1 to apply to all datasets.')
@click.option('--force', help="Regenerate preview for all resources",
              is_flag=True)
@click.command()
def run_jobs_dc_view(modified_days=-1, force=False):
    """Generate preview image for all RT-DC resources

    This also happens for draft datasets.
    """
    # go through all datasets
    datasets = model.Session.query(model.Package)

    if modified_days >= 0:
        # Search only the last `days` days.
        past = datetime.date.today() - datetime.timedelta(days=modified_days)
        past_str = time.strftime("%Y-%m-%d", past.timetuple())
        datasets = datasets.filter(model.Package.metadata_modified >= past_str)

    job_list = jobs.RQJob.get_all_job_methods_in_order(
        ckanext="dc_view")

    nl = False  # new line character
    for dataset in datasets:
        nl = False
        click.echo(f"Checking dataset {dataset.id}\r", nl=False)

        for resource in dataset.resources:
            res_dict = resource.as_dict()
            try:
                for job in job_list:
                    if job.method(res_dict, override=force):
                        if not nl:
                            click.echo("")
                            nl = True
                        click.echo(f"OK: {job.title} for {resource.name}")
            except KeyboardInterrupt:
                raise
            except BaseException as e:
                click.echo(
                    f"\n{e.__class__.__name__} for {res_dict['name']}!",
                    err=True)
                click.echo(traceback.format_exc(), err=True)
                nl = True
    if not nl:
        click.echo("")
    click.echo("Done!")


def get_commands():
    return [run_jobs_dc_view]
