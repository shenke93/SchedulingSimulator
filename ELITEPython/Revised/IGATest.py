import unittest
from datetime import timedelta, datetime

from IGA import ceil_dt, floor_dt, read_product_related_characteristics, read_maintenance, read_price, read_job
from IGA import select_jobs

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
        
    def testReadMaintenance(self):
        input_file = 'maintenanceFileTest.csv'
        res = read_maintenance(input_file)
        self.assertEqual(res[2], 0.020708563905096837)
        
    def testReadPrice(self):
        input_file = 'priceFileTest.csv'
        res = read_price(input_file)
        self.assertEqual(res.get(datetime(2016, 1, 1, 3, 0, 0, 0)), 16.81) 
        
    def testReadJob(self):
        input_file = 'jobFileTest.csv'
        res = read_job(input_file)
        self.assertEqual(res.get(1)[-1], 'FF029001') 
        
    def testSelectJobs(self):
        test_dict = {1:[1, datetime(2016, 1, 1, 3, 0, 0, 0), datetime(2016, 1, 1, 6, 0, 0, 0)], 
                2: [2, datetime(2016, 1, 1, 4, 0, 0, 0), datetime(2016, 1, 1, 5, 0, 0, 0)]}
        res = select_jobs(datetime(2016, 1, 1, 4, 0, 0, 0), datetime(2016, 1, 1, 5, 0, 0, 0), test_dict)
        self.assertEqual(len(res), 1)
        
    
