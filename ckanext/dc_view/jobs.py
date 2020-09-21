import atexit
from collections import OrderedDict
import os
import shutil
import tempfile

import dclab
from dcor_shared import DC_MIME_TYPES, get_resource_path, wait_for_resource
import numpy as np

# Create a temporary matplotlib config directory which is removed on exit
mpldir = tempfile.mkdtemp(prefix="ckan_dcor_dc_view_")
atexit.register(shutil.rmtree, mpldir)
os.environ['MPLCONFIGDIR'] = mpldir

from matplotlib.gridspec import GridSpec  # noqa: E402
import matplotlib  # noqa: E402
matplotlib.use('agg')
import matplotlib.pylab as plt  # noqa: E402


def create_preview_job(resource, override=False):
    """Generate a *_preview.png file for a DC resource"""
    path = get_resource_path(resource["id"])
    wait_for_resource(path)
    mtype = resource.get('mimetype', '')
    if mtype in DC_MIME_TYPES:
        # only do this for rtdc data
        jpgpath = path.with_name(path.name + "_preview.jpg")
        if not jpgpath.exists() or override:
            generate_preview(path, jpgpath)


def generate_preview(path_rtdc, path_jpg):
    # Check whether we have a condensed version of the dataset.
    # If so, also pass that to overview_plot.
    path_condensed = path_rtdc.with_name(path_rtdc.name + "_condensed.rtdc")
    if path_condensed.exists():
        dsc = dclab.rtdc_dataset.fmt_hdf5.RTDC_HDF5(path_condensed)
    else:
        dsc = None
    # This is the original dataset
    ds = dclab.rtdc_dataset.fmt_hdf5.RTDC_HDF5(path_rtdc)
    fig = overview_plot(ds, dsc=dsc)
    fig.savefig(str(path_jpg), dpi=80)
    plt.close()


def overview_plot(ds, dsc=None):
    """Simple overview plot adapted from the dclab examples"""
    if dsc is None:
        dsc = ds
    # Features for scatter plot
    SCATTER_X = "area_um"
    if "bright_avg" in ds:
        SCATTER_Y = "bright_avg"
        ylabel = "Brightness [a.u]"
    else:
        SCATTER_Y = "deform"
        ylabel = dclab.dfn.get_feature_label(SCATTER_Y, rtdc_ds=ds)
    # Event index to display
    EVENT_INDEX = min(len(ds)-1, 47)

    xlabel = dclab.dfn.get_feature_label(SCATTER_X, rtdc_ds=ds)

    plots = OrderedDict()
    plots["scatter_basic"] = SCATTER_X in ds and SCATTER_Y in ds
    plots["scatter_kde"] = SCATTER_X in ds and SCATTER_Y in ds
    plots["image"] = "image" in ds
    plots["mask"] = "mask" in ds
    plots["trace"] = "trace" in ds

    numplots = sum(plots.values())

    height_ratios = []
    for key in plots:
        if plots[key]:
            if key in ["image", "mask"]:
                height_ratios.append(1)
            else:
                height_ratios.append(2)

    fig = plt.figure(figsize=(4, np.sum(height_ratios)*1.5))

    gs = GridSpec(numplots, 1, height_ratios=height_ratios)
    ii = 0

    if SCATTER_X in ds and SCATTER_Y in ds:
        ax1 = fig.add_subplot(gs[ii])
        ax1.set_title("Basic scatter plot")
        ii += 1
        x_start = np.percentile(dsc[SCATTER_X], 1)
        x_end = np.percentile(dsc[SCATTER_X], 99)
        y_start = np.percentile(dsc[SCATTER_Y], 1)
        y_end = np.percentile(dsc[SCATTER_Y], 99)

        ax1.plot(dsc[SCATTER_X], dsc[SCATTER_Y],
                 "o", color="k", alpha=.2, ms=1)
        ax1.set_xlabel(xlabel)
        ax1.set_ylabel(ylabel)
        ax1.set_xlim(x_start, x_end)
        ax1.set_ylim(y_start, y_end)

        ax2 = fig.add_subplot(gs[ii])
        ax2.set_title("KDE scatter plot")
        ii += 1
        sc = ax2.scatter(dsc[SCATTER_X], dsc[SCATTER_Y],
                         c=ds.get_kde_scatter(xax=SCATTER_X,
                                              yax=SCATTER_Y,
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
        ax3.imshow(ds["image"][EVENT_INDEX], cmap="gray")
        ax3.set_xlabel("Detector X [px]")
        ax3.set_ylabel("Detector Y [px]")

        if "contour" in ds:
            ax3.plot(ds["contour"][EVENT_INDEX][:, 0],
                     ds["contour"][EVENT_INDEX][:, 1],
                     c="r")

    if "mask" in ds:
        ax4 = fig.add_subplot(gs[ii])
        ax4.set_title("Event mask")
        ii += 1
        pxsize = ds.config["imaging"]["pixel size"]
        ax4.imshow(ds["mask"][EVENT_INDEX],
                   extent=[0, ds["mask"].shape[2] * pxsize,
                           0, ds["mask"].shape[1] * pxsize],
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
            ax5.plot(fltime, ds["trace"]["fl1_raw"][EVENT_INDEX],
                     c="#15BF00", label="fl1_raw")
        if "fl2_raw" in ds["trace"]:
            ax5.plot(fltime, ds["trace"]["fl2_raw"][EVENT_INDEX],
                     c="#BF8A00", label="fl2_raw")
        if "fl3_raw" in ds["trace"]:
            ax5.plot(fltime, ds["trace"]["fl3_raw"][EVENT_INDEX],
                     c="#BF0C00", label="fl3_raw")
        ax5.legend()
        ax5.set_xlabel(u"Event time [µs]")
        ax5.set_ylabel("Fluorescence [a.u.]")
        ax5.set_xlim(0, fltime[-1])

    plt.tight_layout()

    return fig
