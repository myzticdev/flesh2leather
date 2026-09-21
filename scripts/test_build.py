"""Regression checks for version-specific recipe validation."""
import json
from pathlib import Path
import unittest

from build import check_recipe


class LegacyRecipeTests(unittest.TestCase):
    def setUp(self):
        source = Path(__file__).resolve().parents[1] / 'src'
        self.recipe = json.loads((source / '1.13.x/data/flesh2leather/recipes/'
                                 'rotten_flesh_to_leather.json').read_text())

    def test_plain_serializer_in_1_13(self):
        check_recipe(self.recipe, 4, False, legacy_1_13=True)

    def test_namespaced_serializer_rejected_in_1_13(self):
        self.recipe['type'] = 'minecraft:smelting'
        with self.assertRaises(ValueError):
            check_recipe(self.recipe, 4, False, legacy_1_13=True)

    def test_same_pack_format_does_not_mean_same_serializer(self):
        with self.assertRaises(ValueError):
            check_recipe(self.recipe, 4, False)
        self.recipe['type'] = 'minecraft:smelting'
        check_recipe(self.recipe, 4, False)


if __name__ == '__main__':
    unittest.main()
