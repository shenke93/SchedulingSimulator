import unittest
from datetime import timedelta, datetime

from IGA import ceil_dt, floor_dt, read_product_related_characteristics

class MyTest(unittest.TestCase):
    def testCeilDt(self):
        x1 = datetime(2015, 1, 12, 23, 9, 12, 946118)
        y1 = datetime(2015, 1, 13, 0, 0, 0, 0)
        x2 = datetime(2015, 1, 12, 23, 0, 0, 0)
        y2 = datetime(2015, 1, 12, 23, 0, 0, 0)
        self.assertEqual(ceil_dt(x1, timedelta(hours=1)), y1)
        self.assertEqual(ceil_dt(x2, timedelta(hours=1)), y2)

        
    def testFloorDt(self):
        x1 = datetime(2015, 1, 12, 23, 9, 12, 946118)
        y1 = datetime(2015, 1, 12, 23, 0, 0, 0)
        x2 = datetime(2015, 1, 12, 23, 0, 0, 0)
        y2 = datetime(2015, 1, 12, 23, 0, 0, 0)
        self.assertEqual(floor_dt(x1, timedelta(hours=1)), y1)
        self.assertEqual(ceil_dt(x2, timedelta(hours=1)), y2)
        
    def testReadRroductRelatedCharacteristics(self):
        input_file = 'productFileTest.csv'
        res = read_product_related_characteristics(input_file)
        self.assertEqual(res.get('FF011501'), [0.055,0.13])

