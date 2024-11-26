from collections import OrderedDict
import logging
import os
import pathlib
import shutil
import tempfile

import dclab
from dcor_shared import (
    DC_MIME_TYPES, get_dc_instance, rqjob_register, s3, s3cc, wait_for_resource
)
from dcor_shared import RQJob  # noqa: F401

import numpy as np


log = logging.getLogger(__name__)

# Create a matplotlib config directory, so we can import and use matplotlib
mpldir = "/tmp/matplotlib"
pathlib.Path(mpldir).mkdir(exist_ok=True)
os.environ['MPLCONFIGDIR'] = mpldir

from matplotlib.gridspec import GridSpec  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use('agg')
import matplotlib.pylab as plt  # noqa: E402


def admin_context():
    return {'ignore_auth': True, 'user': 'default'}


@rqjob_register(ckanext="dc_view",
                queue="dcor-normal",
                timeout=3600,
                )
def job_create_preview(resource, override=False):
    """Generate a *_preview.png file for a DC resource"""
    if not s3.is_available():
        log.info("S3 not available, not computing condensed resource")
        return False

    # make sure mimetype is defined
    if "mimetype" not in resource:
        suffix = "." + resource["name"].rsplit(".", 1)[-1]
        for mt in DC_MIME_TYPES:
            if suffix in DC_MIME_TYPES[mt]:
                resource["mimetype"] = mt
                break

    rid = resource["id"]
    wait_for_resource(rid)
    if (resource.get('mimetype', '') in DC_MIME_TYPES
        # Check whether the file already exists on S3
        and (override
             or not s3cc.artifact_exists(resource_id=rid,
                                         artifact="preview"))):
        # Create the preview in a temporary location
        ttd_name = tempfile.mkdtemp(prefix="ckanext-dc_view_")
        try:
            path_preview = pathlib.Path(ttd_name) / "preview.jpg"
            with get_dc_instance(rid) as ds:
                fig = overview_plot(rtdc_ds=ds)
                fig.savefig(str(path_preview), dpi=80)
                plt.close()
            # Upload the preview to S3
            s3cc.upload_artifact(resource_id=rid,
                                 path_artifact=path_preview,
                                 artifact="preview",
                                 override=True)
        except BaseException:
            pass
        else:
            return True
        finally:
            shutil.rmtree(ttd_name, ignore_errors=True)
    return False


def overview_plot(rtdc_ds):
    """Simple overview plot adapted from the dclab examples

    Parameters
    ----------
    rtdc_ds: dclab.rtdc_dataset.core.RTDCBase
        Full RT-DC dataset to plot

    .. versionchanged:: 0.5.10

        Only the first 5000 events are plotted for performance reasons

    .. verionchanged:: 0.8.1

        Removed `rtdc_ds_cond` argument, since we are now working
        with linked datasets.

    """
    # Only plot the first 5000 events
    size = min(len(rtdc_ds), 5000)
    rtdc_ds.filter.manual[:] = False
    rtdc_ds.filter.manual[:size] = True
    rtdc_ds.apply_filter()
    ds = dclab.new_dataset(rtdc_ds)

    # Features for scatter plot
    scatter_x = "area_um"
    scatter_y = "deform"
    # Event index to display
    event_index = min(len(ds) - 1, 47)

    xlabel = dclab.dfn.get_feature_label(scatter_x, rtdc_ds=ds)
    ylabel = dclab.dfn.get_feature_label(scatter_y, rtdc_ds=ds)

    plots = OrderedDict()
    plots["scatter_basic"] = scatter_x in ds and scatter_y in ds
    plots["scatter_kde"] = scatter_x in ds and scatter_y in ds
    plots["image"] = "image" in ds
    plots["mask"] = "mask" in ds
    plots["trace"] = "trace" in ds

    numplots = sum(plots.values())

    if not numplots:
        # empty plot
        fig = plt.figure(figsize=(4, 4))
        return fig

    height_ratios = []
    for key in plots:
        if plots[key]:
            if key in ["image", "mask"]:
                height_ratios.append(1)
            else:
                height_ratios.append(2)

    fig = plt.figure(figsize=(4, np.sum(height_ratios) * 1.5))

    gs = GridSpec(numplots, 1, height_ratios=height_ratios)
    ii = 0

    if scatter_x in ds and scatter_y in ds:
        ax1 = fig.add_subplot(gs[ii])
        ax1.set_title("Basic scatter plot")
        ii += 1
        x_start = np.percentile(ds[scatter_x], 1)
        x_end = np.percentile(ds[scatter_x], 99)
        y_start = np.percentile(ds[scatter_y], 1)
        y_end = np.percentile(ds[scatter_y], 99)

        ax1.plot(ds[scatter_x], ds[scatter_y],
                 "o", color="k", alpha=.2, ms=1)
        ax1.set_xlabel(xlabel)
        ax1.set_ylabel(ylabel)
        ax1.set_xlim(x_start, x_end)
        ax1.set_ylim(y_start, y_end)

        ax2 = fig.add_subplot(gs[ii])
        ax2.set_title("KDE scatter plot")
        ii += 1
        sc = ax2.scatter(ds[scatter_x], ds[scatter_y],
                         c=ds.get_kde_scatter(xax=scatter_x,
                                              yax=scatter_y,
                                              kde_type="histogram"),
                         s=3)
        plt.colorbar(sc, label="kernel density [a.u]", ax=ax2)
        ax2.set_xlabel(xlabel)
        ax2.set_ylabel(ylabel)
        ax2.set_xlim(x_start, x_end)
        ax2.set_ylim(y_start, y_end)

    if "image" in ds:
        ax3 = fig.add_subplot(gs[ii])
        ax3.set_title("Event image with contour")
        ii += 1
        ax3.imshow(ds["image"][event_index], cmap="gray")
        ax3.set_xlabel("Detector X [px]")
        ax3.set_ylabel("Detector Y [px]")

        if "contour" in ds:
            ax3.plot(ds["contour"][event_index][:, 0],
                     ds["contour"][event_index][:, 1],
                     c="r")

    if "mask" in ds:
        ax4 = fig.add_subplot(gs[ii])
        ax4.set_title("Event mask")
        ii += 1
        pxsize = ds.config["imaging"]["pixel size"]
        ax4.imshow(ds["mask"][event_index],
                   extent=(0, ds["mask"][0].shape[1] * pxsize,
                           0, ds["mask"][0].shape[0] * pxsize),
                   cmap="gray")
        ax4.set_xlabel(u"Detector X [µm]")
        ax4.set_ylabel(u"Detector Y [µm]")

    if "trace" in ds:
        ax5 = fig.add_subplot(gs[ii])
        ax5.set_title("Fluorescence traces")
        ii += 1
        flsamples = ds.config["fluorescence"]["samples per event"]
        flrate = ds.config["fluorescence"]["sample rate"]
        fltime = np.arange(flsamples) / flrate * 1e6
        if "fl1_raw" in ds["trace"]:
            ax5.plot(fltime, ds["trace"]["fl1_raw"][event_index],
                     c="#15BF00", label="fl1_raw")
        if "fl2_raw" in ds["trace"]:
            ax5.plot(fltime, ds["trace"]["fl2_raw"][event_index],
                     c="#BF8A00", label="fl2_raw")
        if "fl3_raw" in ds["trace"]:
            ax5.plot(fltime, ds["trace"]["fl3_raw"][event_index],
                     c="#BF0C00", label="fl3_raw")
        ax5.legend()
        ax5.set_xlabel(u"Event time [µs]")
        ax5.set_ylabel("Fluorescence [a.u.]")
        ax5.set_xlim(0, fltime[-1])

    plt.tight_layout()

    return fig
