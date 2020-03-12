# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest
from numpy.testing import assert_allclose
import numpy as np
import astropy.units as u
from gammapy.datasets import MapDataset, MapDatasetOnOff
from gammapy.estimators import CorrelatedExcessMapEstimator
from gammapy.maps import Map, MapAxis, WcsGeom
from gammapy.utils.testing import requires_data
from gammapy.modeling.models import BackgroundModel

def image_to_cube(input_map, e_min, e_max):
    e_min = u.Quantity(e_min)
    e_max = u.Quantity(e_max)
    axis = MapAxis.from_energy_bounds(e_min, e_max, nbin=1)
    geom = input_map.geom.to_cube([axis])
    return Map.from_geom(geom, data=map.data[np.newaxis,:,:])

@pytest.fixture
def simple_dataset():
    axis = MapAxis.from_energy_bounds(0.1, 10, 1, unit="TeV")
    geom = WcsGeom.create(npix=50, binsz=0.02, axes=[axis])
    dataset = MapDataset.create(geom)
    dataset.mask_safe += 1
    dataset.counts += 2
    dataset.background_model.map += 1
    return dataset


@pytest.fixture
def simple_dataset_on_off():
    axis = MapAxis.from_energy_bounds(0.1, 10, 1, unit="TeV")
    geom = WcsGeom.create(npix=50, binsz=0.02, axes=[axis])
    dataset = MapDatasetOnOff.create(geom)
    dataset.mask_safe += 1
    dataset.counts += 2
    dataset.counts_off += 1
    dataset.acceptance += 1
    dataset.acceptance_off += 1
    return dataset


@requires_data()
def test_compute_lima_image():
    """
    Test Li & Ma image against TS image for Tophat kernel
    """
    filename = "$GAMMAPY_DATA/tests/unbundled/poisson_stats_image/input_all.fits.gz"
    counts = Map.read(filename, hdu="counts")
    counts = image_to_cube(counts, '1 GeV', '100 GeV')
    background = Map.read(filename, hdu="background")
    background = image_to_cube(background, '1 GeV', '100 GeV')
    background_model = BackgroundModel(background)
    dataset = MapDataset(counts=counts)
    dataset.models =background_model

    estimator = CorrelatedExcessMapEstimator(dataset,'0.1 deg')
    result_lima = estimator.run( steps="ts")

    assert_allclose(result_lima["significance"].data[:,100, 100], 30.814916, atol=1e-3)
    assert_allclose(result_lima["significance"].data[:,1, 1], 0.164, atol=1e-3)


@requires_data()
def test_compute_lima_on_off_image():
    """
    Test Li & Ma image with snippet from the H.E.S.S. survey data.
    """
    filename = "$GAMMAPY_DATA/tests/unbundled/hess/survey/hess_survey_snippet.fits.gz"
    n_on = Map.read(filename, hdu="ON")
    counts = image_to_cube(n_on, '1 TeV', '100 TeV')
    n_off = Map.read(filename, hdu="OFF")
    counts_off = image_to_cube(n_off, '1 TeV', '100 TeV')
    a_on = Map.read(filename, hdu="ONEXPOSURE")
    acceptance = image_to_cube(a_on, '1 TeV', '100 TeV')
    a_off = Map.read(filename, hdu="OFFEXPOSURE")
    acceptance_off = image_to_cube(a_off, '1 TeV', '100 TeV')
    dataset = MapDatasetOnOff(
        counts=counts,
        counts_off=counts_off,
        acceptance=acceptance,
        acceptance_off=acceptance_off
    )

    significance = Map.read(filename, hdu="SIGNIFICANCE")
    significance = image_to_cube(significance, '1 TeV', '10 TeV')
    estimator = CorrelatedExcessMapEstimator(dataset, '0.1 deg')
    results = estimator.run(steps="ts")

    # Reproduce safe significance threshold from HESS software
    results["significance"].data[results["counts"].data < 5] = 0

    # crop the image at the boundaries, because the reference image
    # is cut out from a large map, there is no way to reproduce the
    # result with regular boundary handling
    actual = results["significance"].crop((11,11)).data
    desired = significance.crop((11,11)).data

    # Set boundary to NaN in reference image
    # The absolute tolerance is low because the method used here is slightly different from the one used in HGPS
    # n_off is convolved as well to ensure the method applies to true ON-OFF datasets
    assert_allclose(actual, desired, atol=0.2)


def test_significance_map_estimator_incorrect_dataset():
    with pytest.raises(ValueError):
        CorrelatedExcessMapEstimator("bad")

def test_significance_map_estimator_map_dataset(simple_dataset):
    estimator = CorrelatedExcessMapEstimator(simple_dataset, 0.1 * u.deg)
    result = estimator.run(steps=["ts"])

    assert_allclose(result["counts"].data[0, 25, 25], 162)
    assert_allclose(result["excess"].data[0, 25, 25], 81)
    assert_allclose(result["background"].data[0, 25, 25], 81)
    assert_allclose(result["significance"].data[0, 25, 25], 7.910732, atol=1e-5)


def test_significance_map_estimator_map_dataset_on_off(simple_dataset_on_off):
    estimator = CorrelatedExcessMapEstimator(simple_dataset_on_off, 0.11 * u.deg)
    result = estimator.run(steps=["ts"])

    assert_allclose(result["counts"].data[0, 25, 25], 194)
    assert_allclose(result["excess"].data[0, 25, 25], 97)
    assert_allclose(result["background"].data[0, 25, 25], 97)
    assert_allclose(result["significance"].data[0, 25, 25], 5.741116, atol=1e-5)
