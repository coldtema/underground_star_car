import requests
import math
from ..models import Car
import asyncio
import aiohttp
from django.db import transaction

diagnosis = 'https://api.encar.com/v1/readside/diagnosis/vehicle/40286929'

car_info = 'https://api.encar.com/v1/readside/vehicle/40294388'

photos = 'https://ci.encar.com/carpicture/carpicture03/pic4003/40034021_001.jpg?impolicy=heightRate&rh=696&cw=1160&ch=696&cg=Center&wtmk=https://ci.encar.com/wt_mark/w_mark_04.png'




class AsyncCarClearer():
    def __init__(self):
        self.batch_size = 1000
        self.session = requests.Session()
        self.encar_api_url = 'https://api.encar.com/v1/readside/vehicle/'
        self.car_count = Car.objects.all().count()
        self.encar_ids = Car.objects.all().values('encar_id')
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
            self.batch = Car.objects.filter(encar_id__in=self.encar_ids[i*self.batch_size:(i+1)*self.batch_size])
            self.go_through_batch()
            self.save_to_db()


    def go_through_batch(self):
        list_api_urls = []
        for car in self.batch:
            list_api_urls.append(f'{self.encar_api_url}{car.encar_id}')
        print(f'Запуск {self.counter}')
        self.counter += 1
        self.results = asyncio.run(self.get_info(list_api_urls))
        
    

    async def fetch(self, session, url):
        try:
            async with session.get(url, timeout=10) as response:
                response = await response.json()
                if response['advertisement']['status'] == 'ADVERTISE':
                        return int(url.split('/')[-1]), True
                return int(url.split('/')[-1]), False
        except:
            return int(url.split('/')[-1]), False 


    async def get_info(self, batch):
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.session.cookies) as session:
            tasks = [self.fetch(session, url) for url in batch]
            results = await asyncio.gather(*tasks)
            return results
    

    def get_cookies(self):
        self.session.get("https://www.encar.com", headers=self.headers) 


    @transaction.atomic
    def save_to_db(self):
        self.cars_ids_to_delete = []
        for result in self.results:
            if result[1] == False:
                self.cars_ids_to_delete.append(result[0])
        if self.cars_ids_to_delete:
            print(self.cars_ids_to_delete)
            Car.objects.filter(encar_id__in=self.cars_ids_to_delete).delete()
        self.results = []