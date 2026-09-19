import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('builder', Path(__file__).resolve().parents[1] / 'build_keyword_workbook.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

class RootBrandPhraseTests(unittest.TestCase):
    def test_multiword_brand_preserves_generic_product_roots(self):
        vocab = {key: set() for key in ('brand', 'claim', 'form', 'negative', 'explicit_never', 'related_excludes', 'core_words', 'listing_words', 'poe_words', 'relevant')}
        vocab['brand'] = {'one size', 'elf'}
        vocab['core_words'] = {'pink', 'powder', 'size'}
        self.assertEqual(b._root_category('one size pink powder', vocab), 'Brand')
        self.assertEqual(b._root_category('elf pink powder', vocab), 'Brand')
        self.assertEqual(b._root_category('pink powder', vocab), 'Core/Product')
        self.assertEqual(b._root_category('travel size powder', vocab), 'Core/Product')
        self.assertEqual(b._root_category('selfie powder', vocab), 'Core/Product')

if __name__ == '__main__':
    unittest.main()
