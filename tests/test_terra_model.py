import unittest

import numpy as np

from terratools import terra_model
from terratools.terra_model import TerraModel

# Tolerance for match of floating point numbers, given that TerraModel
# coordinates and values have a defined precision
coord_tol = np.finfo(terra_model.COORDINATE_TYPE).eps
value_tol = np.finfo(terra_model.VALUE_TYPE).eps

# Helper functions for the tests
def dummy_model(nlayers=3, npts=4, with_fields=False, **kwargs):
    lon, lat, r = random_coordinates(nlayers, npts)
    if with_fields:
        fields = {"t": random_field(nlayers, npts), "u_xyz": random_field(nlayers, npts, 3)}
    else:
        fields = {}
    return TerraModel(lon, lat, r, fields=fields, **kwargs)

def random_coordinates(nlayers, npts):
    """Return a set of random coordinates (satisfying the constraints)
    which can be passed to construct a TerraModel.
    FIXME: In theory there may be duplicate points as they are random."""
    rmin, rmax = np.sort(7000*np.random.rand(2))
    r = np.sort(np.random.uniform(rmin, rmax, nlayers))
    lon = 360*(np.random.rand(npts) - 0.5)
    lat = 180*(np.random.rand(npts) - 0.5)
    return lon, lat, r

def random_field(nlayers, npts, ncomps=None):
    if ncomps is None:
        return np.random.rand(nlayers, npts)
    else:
        return np.random.rand(nlayers, npts, ncomps)

def fields_are_equal(field1, field2):
    return np.allclose(field1, field2, atol=value_tol)

def coords_are_equal(coords1, coords2):
    return np.allclose(coords1, coords2, atol=coord_tol)


class TestTerraModelHelpers(unittest.TestCase):
    """Tests for non-class methods"""

    def test_is_valid_field_name(self):
        """Test for validity of a field name"""
        self.assertFalse(terra_model._is_valid_field_name("incorrect field name"))
        self.assertTrue(terra_model._is_valid_field_name("t"))

    def test_variable_name_from_field(self):
        """Translation of field name to NetCDF variable name(s)"""
        self.assertEqual(terra_model._variable_names_from_field("t"),
            ("Temperature",))
        self.assertEqual(terra_model._variable_names_from_field("u_xyz"),
            ("Velocity_x", "Velocity_y", "Velocity_z"))
        self.assertEqual(terra_model._variable_names_from_field("c_hist"),
            ("BasaltFrac", "LherzFrac"))
        with self.assertRaises(KeyError):
            terra_model._variable_names_from_field("incorrect field name")

    def test_field_name_from_variable(self):
        """Translation of NetCDF variable name to field name"""
        self.assertEqual(terra_model._field_name_from_variable("Temperature"), "t")

    def test_check_field_name(self):
        self.assertEqual(terra_model._check_field_name("vp"), None)
        with self.assertRaises(terra_model.FieldNameError):
            terra_model._check_field_name("incorrect field name")

    def test_is_scalar_field(self):
        self.assertTrue(terra_model._is_scalar_field("c"))
        self.assertFalse(terra_model._is_scalar_field("c_hist"))

    def test_is_vector_field(self):
        self.assertTrue(terra_model._is_vector_field("u_xyz"))
        self.assertFalse(terra_model._is_vector_field("t"))

    def test_expected_vector_field_ncomps(self):
        self.assertEqual(terra_model._expected_vector_field_ncomps("u_xyz"), 3)
        self.assertEqual(terra_model._expected_vector_field_ncomps("u_geog"), 3)
        self.assertEqual(terra_model._expected_vector_field_ncomps("c_hist"), None)


class TestTerraModelConstruction(unittest.TestCase):
    """Tests for construction and validation of fields"""

    def test_invalid_field_dimensions(self):
        npts = 3
        nlayers = 2
        scalar_field = random_field(nlayers, npts)
        vector_field = random_field(nlayers, npts, 3)
        fields = {"t": scalar_field, "u_xyz": vector_field}

        with self.assertRaises(terra_model.FieldDimensionError):
            lon, lat, r = random_coordinates(nlayers, npts + 1)
            TerraModel(lon, lat, r, fields=fields)

        with self.assertRaises(terra_model.FieldDimensionError):
            lon, lat, r = random_coordinates(nlayers, npts - 1)
            TerraModel(lon, lat, r, fields=fields)

        with self.assertRaises(terra_model.FieldDimensionError):
            lon, lat, r = random_coordinates(nlayers + 1, npts)
            TerraModel(lon, lat, r, fields=fields)

        with self.assertRaises(terra_model.FieldDimensionError):
            lon, lat, r = random_coordinates(nlayers - 1, npts)
            TerraModel(lon, lat, r, fields=fields)

    def test_invalid_field_name(self):
        npts = 10
        nlayers = 3
        field = random_field(nlayers, npts)
        lon, lat, r = random_coordinates(nlayers, npts)
        with self.assertRaises(terra_model.FieldNameError):
            TerraModel(lon, lat, r, fields={"incorrect field name": field})

    def test_invalid_ncomps(self):
        nlayers = 3
        npts = 2
        u_xyz = random_field(nlayers, npts, 2)
        lon, lat, r = random_coordinates(nlayers, npts)
        with self.assertRaises(terra_model.FieldDimensionError):
            TerraModel(lon, lat, r, fields={"u_xyz": u_xyz})

    def test_radii_not_motonic(self):
        with self.assertRaises(ValueError):
            TerraModel([1], [1], [1, 3, 2])

    def test_radii_not_increasing(self):
        with self.assertRaises(ValueError):
            TerraModel([1], [1], [3, 2, 1])

    def test_lon_lat_not_same_length(self):
        with self.assertRaises(ValueError):
            TerraModel([1], [2,3], [1,2,3])

    def test_construction(self):
        """Ensure the things we pass in are put in the right place"""
        nlayers = 3
        npts = 10
        lon, lat, r = random_coordinates(nlayers, npts)
        scalar_field_names = ("t", "c", "vp", "vs", "density", "p")
        scalar_fields = [random_field(nlayers, npts) for _ in scalar_field_names]
        u_field = random_field(nlayers, npts, 3)
        c_hist_field = random_field(nlayers, npts, 2)
        fields = {name: field for name, field in zip(scalar_field_names, scalar_fields)}
        fields["u_xyz"] = u_field
        fields["u_geog"] = u_field
        fields["c_hist"] = c_hist_field
        c_hist_names = ["A", "B"]

        model = TerraModel(lon, lat, r, fields=fields, c_histogram_names=c_hist_names)

        _lon, _lat = model.get_lateral_points()
        self.assertTrue(coords_are_equal(lon, _lon))
        self.assertTrue(coords_are_equal(lat, _lat))

        self.assertTrue(coords_are_equal(model.get_radii(), r))

        for (field_name, field) in zip(scalar_field_names, scalar_fields):
            self.assertTrue(fields_are_equal(model.get_field(field_name), field))

        self.assertTrue(fields_are_equal(model.get_field("c_hist"), c_hist_field))

        for field in ("u_xyz", "u_geog"):
            self.assertTrue(fields_are_equal(model.get_field(field), u_field))

        self.assertTrue(fields_are_equal(model.get_field("c_hist"), c_hist_field))
        self.assertEqual(model.number_of_compositions(), 2)
        self.assertEqual(model.get_composition_names(), ["A", "B"])

        # Use set because we don't need to enforce that the fields
        # are in the same order
        self.assertEqual(set(model.field_names()), set(fields.keys()))

        for field in (*scalar_field_names, "u_geog", "u_xyz", "c_hist"):
            self.assertTrue(model.has_field(field))
        self.assertFalse(model.has_field("vs_an"))


class TestTerraModelGetters(unittest.TestCase):
    """Tests for getters"""

    def test_invalid_field_name(self):
        """Check that an error is thrown when asking for an invalid field"""
        model = dummy_model()
        model.new_field("t")
        with self.assertRaises(terra_model.FieldNameError):
            model.evaluate(0, 0, 4000, "incorrect field name")

    def test_missing_field(self):
        model = dummy_model()
        model.new_field("t")
        with self.assertRaises(terra_model.NoFieldError):
            model.evaluate(0, 0, 4000, "u_xyz")

    def test_get_field(self):
        model = dummy_model(with_fields=True)
        self.assertIs(model.get_field("t"), model._fields["t"])

        temp = model.get_field("t")
        temp[0,0] = 1
        self.assertTrue(np.all(model.get_field("t") == temp))

    def test_get_radii(self):
        r = [1,2,3]
        model = TerraModel([1,2], [3,4], r)
        self.assertIs(model.get_radii(), model._radius)

    def test_get_lateral_points(self):
        lon, lat, r = random_coordinates(3, 4)
        model = TerraModel(lon, lat, r)
        _lon, _lat = model.get_lateral_points()
        self.assertIs(_lon, model._lon)
        self.assertIs(_lat, model._lat)

    def test_get_composition_names(self):
        model = dummy_model(c_histogram_names=["A", "B"])
        model.new_field("c_hist", 2)
        self.assertEqual(model.get_composition_names(), ["A", "B"])


class TestTerraModelNewField(unittest.TestCase):
    def test_wrong_ncomps(self):
        model = dummy_model()
        with self.assertRaises(ValueError):
            model.new_field("t", 1)
        with self.assertRaises(ValueError):
            model.new_field("u_xyz", 4)

    def test_no_ncomps(self):
        model = dummy_model()
        with self.assertRaises(ValueError):
            model.new_field("c_hist")

    def test_new_field(self):
        model = dummy_model()
        nlayers = len(model.get_radii())
        npts = len(model.get_lateral_points()[0])

        self.assertFalse(model.has_field("t"))
        self.assertFalse(model.has_field("u_xyz"))
        self.assertFalse(model.has_field("c_hist"))

        model.new_field("t")
        self.assertTrue(model.has_field("t"))
        self.assertTrue(
            fields_are_equal(model.get_field("t"), np.zeros((nlayers, npts))))

        model.new_field("u_xyz")
        self.assertTrue(model.has_field("u_xyz"))
        self.assertTrue(
            fields_are_equal(model.get_field("u_xyz"), np.zeros((nlayers, npts, 3))))

        model.new_field("c_hist", 2)
        self.assertTrue(model.has_field("c_hist"))
        self.assertTrue(
            fields_are_equal(model.get_field("c_hist"), np.zeros((nlayers, npts, 2))))


class TestTerraModelRepr(unittest.TestCase):
    def test_repr(self):
        npts = 3
        nlayers = 3
        lon = [1, 2, 3]
        lat = [10, 20, 30]
        r = [1000, 1999, 2000]
        t_field = random_field(nlayers, npts)
        c_hist_field = random_field(nlayers, npts, 2)
        cnames = ["a", "b"]
        model = TerraModel(lon, lat, r, fields={"t": t_field, "c_hist": c_hist_field},
            c_histogram_names=cnames)

        self.assertEqual(model.__repr__(),
            """TerraModel:
           number of radii: 3
             radius limits: (1000.0, 2000.0)
  number of lateral points: 3
                    fields: ['t', 'c_hist']
         composition names: ['a', 'b']""")


class TestTerraModelNearestIndex(unittest.TestCase):
    def test_nearest_index(self):
        lon = [20, 22, 0.1, 25]
        lat = [20, 22, 0.1, 24]
        r = [10, 20]
        model = TerraModel(lon, lat, r)
        self.assertEqual(model.nearest_index(0, 0), 2)


if __name__ == '__main__':
    unittest.main()
