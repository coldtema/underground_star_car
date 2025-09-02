import requests
import math
from ..models import Car, Diagnosis
import asyncio
import aiohttp
from django.db import transaction

diagnosis1 = 'https://api.encar.com/v1/readside/diagnosis/vehicle/40286929'

car_info = 'https://api.encar.com/v1/readside/vehicle/38877922'

photos = 'https://ci.encar.com/carpicture/carpicture03/pic4003/40034021_001.jpg?impolicy=heightRate&rh=696&cw=1160&ch=696&cg=Center&wtmk=https://ci.encar.com/wt_mark/w_mark_04.png'




class AsyncCarDiagParser():
    def __init__(self):
        self.batch_size = 1000
        self.session = requests.Session()
        self.encar_api_url = 'https://api.encar.com/v1/readside/diagnosis/vehicle/'
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
            self.batch = Car.objects.filter(dummy_id__in=self.dummy_ids[i*self.batch_size:(i+1)*self.batch_size], encar_diag__gt=-1, diagnosis__isnull=True)
            self.go_through_batch()
            self.save_to_db()


    def go_through_batch(self):
        list_api_urls = []
        for car in self.batch:
            list_api_urls.append(f'{self.encar_api_url}{car.dummy_id}')
        print(f'Запуск {self.counter}')
        self.counter += 1
        self.results = asyncio.run(self.get_info(list_api_urls))
        
    

    async def fetch(self, session, url):
        async with session.get(url, timeout=10) as response:
            response = await response.json()
            items = response['items']
            diag_dict = dict()
            for item in items:
                diag_dict.setdefault(item['name'], item['resultCode'])
            diag_dict['dummy_id'] = response['vehicleId']
            return diag_dict


    async def get_info(self, batch):
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.session.cookies) as session:
            tasks = [self.fetch(session, url) for url in batch]
            results = await asyncio.gather(*tasks)
            return results
    

    def get_cookies(self):
        self.session.get("https://www.encar.com", headers=self.headers) 

    @transaction.atomic
    def save_to_db(self):
        self.updated_batch = []
        for result in self.results:
            car_to_update = self.batch.get(dummy_id=result['dummy_id'])
            self.updated_batch.append(Diagnosis(
                left_front_door=result['FRONT_DOOR_LEFT'],
                left_back_door=result['BACK_DOOR_LEFT'],
                right_front_door=result['FRONT_DOOR_RIGHT'],
                right_back_door=result['BACK_DOOR_RIGHT'],
                trunk=result['TRUNK_LID'],
                hood=result['HOOD'],
                front_fender_right=result['FRONT_FENDER_RIGHT'],
                front_fender_left=result['FRONT_FENDER_LEFT'],
                car=car_to_update))
        Diagnosis.objects.bulk_create(self.updated_batch)
        self.results = []
