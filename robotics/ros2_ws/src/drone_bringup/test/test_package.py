import unittest


class TestDroneBringupPackage(unittest.TestCase):
    def test_drone_bringup_package_import(self) -> None:
        import drone_bringup

        self.assertEqual(drone_bringup.__name__, "drone_bringup")


if __name__ == "__main__":
    unittest.main()
