# Copyright (c) 2010-2023 Satpy developers
#
# This file is part of satpy.
#
# satpy is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# satpy is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# satpy.  If not, see <http://www.gnu.org/licenses/>.

"""Unit tests for Scene conversion functionality."""

import datetime as dt
from datetime import datetime

import numpy as np
import pytest
import xarray as xr
from dask import array as da

from satpy import Scene
from satpy.tests.utils import skip_numba_unstable_if_missing

# NOTE:
# The following fixtures are not defined in this file, but are used and injected by Pytest:
# - include_test_etc

skip_unstable_numba = pytest.mark.skipif(skip_numba_unstable_if_missing(),
                                         reason="Numba is not compatible with unstable NumPy: {err!s}")


@pytest.mark.usefixtures("include_test_etc")
class TestSceneSerialization:
    """Test the Scene serialization."""

    def test_serialization_with_readers_and_data_arr(self):
        """Test that dask can serialize a Scene with readers."""
        from distributed.protocol import deserialize, serialize

        scene = Scene(filenames=["fake1_1.txt"], reader="fake1")
        scene.load(["ds1"])
        cloned_scene = deserialize(*serialize(scene))
        assert scene._readers.keys() == cloned_scene._readers.keys()
        assert scene.all_dataset_ids == scene.all_dataset_ids


class TestSceneConversions:
    """Test Scene conversion to geoviews, xarray, etc."""

    def test_geoviews_basic_with_area(self):
        """Test converting a Scene to geoviews with an AreaDefinition."""
        from pyresample.geometry import AreaDefinition
        scn = Scene()
        area = AreaDefinition("test", "test", "test",
                              {"proj": "geos", "lon_0": -95.5, "h": 35786023.0},
                              2, 2, [-200, -200, 200, 200])
        scn["ds1"] = xr.DataArray(da.zeros((2, 2), chunks=-1), dims=("y", "x"),
                                  attrs={"start_time": dt.datetime(2018, 1, 1),
                                         "area": area})
        gv_obj = scn.to_geoviews()
        # we assume that if we got something back, geoviews can use it
        assert gv_obj is not None

    def test_geoviews_basic_with_swath(self):
        """Test converting a Scene to geoviews with a SwathDefinition."""
        from pyresample.geometry import SwathDefinition
        scn = Scene()
        lons = xr.DataArray(da.zeros((2, 2)))
        lats = xr.DataArray(da.zeros((2, 2)))
        area = SwathDefinition(lons, lats)
        scn["ds1"] = xr.DataArray(da.zeros((2, 2), chunks=-1), dims=("y", "x"),
                                  attrs={"start_time": dt.datetime(2018, 1, 1),
                                         "area": area})
        gv_obj = scn.to_geoviews()
        # we assume that if we got something back, geoviews can use it
        assert gv_obj is not None

    @skip_unstable_numba
    def test_hvplot_basic_with_area(self):
        """Test converting a Scene to hvplot with a AreaDefinition."""
        from pyresample.geometry import AreaDefinition
        scn = Scene()
        area = AreaDefinition("test", "test", "test",
                              {"proj": "geos", "lon_0": -95.5, "h": 35786023.0},
                              2, 2, [-200, -200, 200, 200])
        scn["ds1"] = xr.DataArray(da.zeros((2, 2), chunks=-1), dims=("y", "x"),
                                  attrs={"start_time": dt.datetime(2018, 1, 1),
                                         "area": area, "units": "m"})
        hv_obj = scn.to_hvplot()
        # we assume that if we got something back, hvplot can use it
        assert hv_obj is not None

    @skip_unstable_numba
    def test_hvplot_rgb_with_area(self):
        """Test converting a Scene to hvplot with a AreaDefinition."""
        from pyresample.geometry import AreaDefinition
        scn = Scene()
        area = AreaDefinition("test", "test", "test",
                              {"proj": "geos", "lon_0": -95.5, "h": 35786023.0},
                              2, 2, [-200, -200, 200, 200])
        scn["ds1"] = xr.DataArray(da.zeros((2, 2), chunks=-1), dims=("y", "x"),
                                  attrs={"start_time": dt.datetime(2018, 1, 1),
                                         "area": area, "units": "m"})
        scn["ds2"] = xr.DataArray(da.zeros((2, 2), chunks=-1), dims=("y", "x"),
                                  attrs={"start_time": dt.datetime(2018, 1, 1),
                                         "area": area, "units": "m"})
        scn["ds3"] = xr.DataArray(da.zeros((2, 2), chunks=-1), dims=("y", "x"),
                                  attrs={"start_time": dt.datetime(2018, 1, 1),
                                         "area": area, "units": "m"})
        hv_obj = scn.to_hvplot()
        # we assume that if we got something back, hvplot can use it
        assert hv_obj is not None

    @skip_unstable_numba
    def test_hvplot_basic_with_swath(self):
        """Test converting a Scene to hvplot with a SwathDefinition."""
        from pyresample.geometry import SwathDefinition
        scn = Scene()
        longitude = xr.DataArray(da.zeros((2, 2)))
        latitude = xr.DataArray(da.zeros((2, 2)))
        area = SwathDefinition(longitude, latitude)
        scn["ds1"] = xr.DataArray(da.zeros((2, 2), chunks=-1), dims=("y", "x"),
                                  attrs={"start_time": dt.datetime(2018, 1, 1),
                                         "area": area, "units": "m"})
        hv_obj = scn.to_hvplot()
        # we assume that if we got something back, hvplot can use it
        assert hv_obj is not None

class TestToXarrayConversion:
    """Test Scene.to_xarray() conversion."""

    def test_with_empty_scene(self):
        """Test converting empty Scene to xarray."""
        scn = Scene()
        ds = scn.to_xarray()
        assert isinstance(ds, xr.Dataset)
        assert len(ds.variables) == 0
        assert len(ds.coords) == 0

    @pytest.fixture
    def single_area_scn(self):
        """Define Scene with single area."""
        from pyresample.geometry import AreaDefinition

        area = AreaDefinition("test", "test", "test",
                              {"proj": "geos", "lon_0": -95.5, "h": 35786023.0},
                              2, 2, [-200, -200, 200, 200])
        data_array = xr.DataArray(da.zeros((2, 2), chunks=-1),
                                  dims=("y", "x"),
                                  attrs={"start_time": dt.datetime(2018, 1, 1), "area": area})
        scn = Scene()
        scn["var1"] = data_array
        return scn

    def test_to_xarray_dataset_with_conflicting_variables(self):
        """Test converting Scene with DataArrays with conflicting variables.

        E.g. "acq_time" in the seviri_l1b_nc reader
        """
        from pyresample.geometry import AreaDefinition
        area = AreaDefinition("test", "test", "test",
                              {"proj": "geos", "lon_0": -95.5, "h": 35786023.0},
                              2, 2, [-200, -200, 200, 200])
        scn = Scene()

        acq_time_1 = ("y", [np.datetime64("1958-01-02 00:00:01"),
                            np.datetime64("1958-01-02 00:00:02")])
        ds = xr.DataArray(da.zeros((2, 2), chunks=-1), dims=("y", "x"),
                attrs={"start_time": datetime(2018, 1, 1), "area": area})
        ds["acq_time"] = acq_time_1

        scn["ds1"] = ds

        acq_time_2 = ("y", [np.datetime64("1958-02-02 00:00:01"),
                            np.datetime64("1958-02-02 00:00:02")])
        ds2 = ds.copy()
        ds2["acq_time"] = acq_time_2

        scn["ds2"] = ds2

        # drop case (compat="minimal")
        xrds = scn.to_xarray_dataset()
        assert isinstance(xrds, xr.Dataset)
        assert "acq_time" not in xrds.coords

        # override: pick variable from first dataset
        xrds = scn.to_xarray_dataset(datasets=["ds1", "ds2"], compat="override")
        assert isinstance(xrds, xr.Dataset)
        assert "acq_time" in xrds.coords
        xr.testing.assert_equal(xrds["acq_time"], ds["acq_time"])

    @pytest.fixture
    def multi_area_scn(self):
        """Define Scene with multiple area."""
        from pyresample.geometry import AreaDefinition

        area1 = AreaDefinition("test", "test", "test",
                               {"proj": "geos", "lon_0": -95.5, "h": 35786023.0},
                               2, 2, [-200, -200, 200, 200])
        area2 = AreaDefinition("test", "test", "test",
                               {"proj": "geos", "lon_0": -95.5, "h": 35786023.0},
                               4, 4, [-200, -200, 200, 200])

        data_array1 = xr.DataArray(da.zeros((2, 2), chunks=-1),
                                   dims=("y", "x"),
                                   attrs={"start_time": dt.datetime(2018, 1, 1), "area": area1})
        data_array2 = xr.DataArray(da.zeros((4, 4), chunks=-1),
                                   dims=("y", "x"),
                                   attrs={"start_time": dt.datetime(2018, 1, 1), "area": area2})
        scn = Scene()
        scn["var1"] = data_array1
        scn["var2"] = data_array2
        return scn

    def test_with_single_area_scene_type(self, single_area_scn):
        """Test converting single area Scene to xarray dataset."""
        ds = single_area_scn.to_xarray()
        assert isinstance(ds, xr.Dataset)
        assert "var1" in ds.data_vars

    def test_include_lonlats_true(self, single_area_scn):
        """Test include lonlats."""
        ds = single_area_scn.to_xarray(include_lonlats=True)
        assert "latitude" in ds.coords
        assert "longitude" in ds.coords

    def test_include_lonlats_false(self, single_area_scn):
        """Test exclude lonlats."""
        ds = single_area_scn.to_xarray(include_lonlats=False)
        assert "latitude" not in ds.coords
        assert "longitude" not in ds.coords

    def test_dataset_string_accepted(self, single_area_scn):
        """Test accept dataset string."""
        ds = single_area_scn.to_xarray(datasets="var1")
        assert isinstance(ds, xr.Dataset)

    def test_wrong_dataset_key(self, single_area_scn):
        """Test raise error if unexisting dataset."""
        with pytest.raises(KeyError):
            _ = single_area_scn.to_xarray(datasets="var2")

    def test_to_xarray_with_multiple_area_scene(self, multi_area_scn):
        """Test converting muiltple area Scene to xarray."""
        # TODO: in future adapt for DataTree implementation
        with pytest.raises(ValueError, match="Datasets to be saved .* must have identical projection coordinates."):
            _ = multi_area_scn.to_xarray()
