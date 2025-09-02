import requests
import math
from ..models import Car, CarRecord, Accident
import asyncio
import aiohttp
from django.db import transaction


record1 = 'https://api.encar.com/v1/readside/record/vehicle/40387760/open?vehicleNo='

sold = 'https://fem.encar.com/cars/detail/39568684'


class AsyncCarRecordParser():
    def __init__(self):
        self.batch_size = 1000
        self.session = requests.Session()
        self.encar_api_url = ['https://api.encar.com/v1/readside/record/vehicle/', '', '/open?vehicleNo=', '']
        self.car_count = Car.objects.all().count()
        self.dummy_ids = Car.objects.all().values('dummy_id')
        self.headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
                    "Referer": "https://www.encar.com/",
                    "Accept": "application/json, text/plain, */*",
        }
        self.batch = []
        self.results = []
        self.counter = 1

    def run(self):
        self.get_cookies()
        print('Куки получены')
        self.batching_query()
        self.session.close()


    def batching_query(self):
        '''Функция прохода через все батчи легковых машин'''
        for i in range(math.ceil(self.car_count/self.batch_size)):
            self.batch = Car.objects.filter(dummy_id__in=self.dummy_ids[i*self.batch_size:(i+1)*self.batch_size], record=1, car_record__isnull=True)
            self.go_through_batch()
            self.save_to_db()


    def go_through_batch(self):
        list_api_urls = []
        for car in self.batch:
            list_api_urls.append(f'{self.encar_api_url[0]}{car.dummy_id}{self.encar_api_url[2]}{car.korean_number}')
        print(f'Запуск {self.counter}')
        self.counter += 1
        self.results = asyncio.run(self.get_info(list_api_urls))
        
    

    async def fetch(self, session, url):
        try:
            async with session.get(url, timeout=10) as response:
                response = await response.json()
                record_dict = dict()
                record_dict['owner_count'] = response['ownerChangeCnt'] + 1
                record_dict['other_accident_cost'] = response['otherAccidentCost']
                record_dict['other_accident_count'] = response['otherAccidentCnt']
                record_dict['driver_accident_cost'] = response['myAccidentCost']
                record_dict['driver_accident_count'] = response['myAccidentCnt']
                record_dict['dummy_id'] = url.split('/')[7]
                record_dict['accidents'] = response['accidents']
                return record_dict
        except:
            print(url)
            return None


    async def get_info(self, batch):
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.session.cookies) as session:
            tasks = [self.fetch(session, url) for url in batch]
            results = await asyncio.gather(*tasks)
            return results
    

    def get_cookies(self):
        self.session.get("https://www.encar.com", headers=self.headers) 

    @transaction.atomic
    def save_to_db(self):
        accidents = []
        for result in self.results:
            if result:
                car_to_update = self.batch.get(dummy_id=result['dummy_id'])
                car_record = CarRecord.objects.create(
                                owner_count = result['owner_count'],
                                other_accident_cost = result['other_accident_cost'],
                                other_accident_count = result['other_accident_count'],
                                driver_accident_cost = result['driver_accident_cost'],
                                driver_accident_count = result['driver_accident_count'],
                                car=car_to_update)
                for accident in result['accidents']:
                    accidents.append(Accident(
                        type_of_accident = accident['type'],
                        date = accident['date'],
                        insurance_benefit = accident['insuranceBenefit'],
                        part_cost = accident['partCost'],
                        labor_cost = accident['laborCost'],
                        painting_cost = accident['paintingCost'],
                        car_record = car_record,
                    ))
        Accident.objects.bulk_create(accidents)
        self.results = []
