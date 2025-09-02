import requests
import math
from ..models import Car, Truck
import asyncio
import aiohttp
from apps.parser.parsers.raw_parser import car_korean_dict
from django.db import transaction

diagnosis = 'https://api.encar.com/v1/readside/diagnosis/vehicle/40286929'

car_info = 'https://api.encar.com/v1/readside/vehicle/39813971'

photos = 'https://ci.encar.com/carpicture/carpicture03/pic4003/40034021_001.jpg?impolicy=heightRate&rh=696&cw=1160&ch=696&cg=Center&wtmk=https://ci.encar.com/wt_mark/w_mark_04.png'




class AsyncCarParser():
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
            self.batch = Car.objects.filter(encar_id__in=self.encar_ids[i*self.batch_size:(i+1)*self.batch_size], manufacturer=None, model=None, version=None, version_details=None)
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
        async with session.get(url, timeout=10) as response:
            response = await response.json()
            photos_codes = list(map(lambda x: x['path'][-7:-4], response['photos']))
            if response['manage']['dummy'] == True: dummy_id = response['vehicleId']
            else: dummy_id = int(url.split('/')[-1])
            detail_dict = {
                'encar_id': int(url.split('/')[-1]), 
                'manufacturer': response['category']['manufacturerEnglishName'],
                'model': response['category']['modelGroupEnglishName'],
                'version': response['category']['gradeEnglishName'],
                'version_details': response['category']['gradeDetailEnglishName'],
                'options': response['options']['standard'],
                'color': response['spec']['colorName'],
                'engine_capacity': response['spec']['displacement'],
                'photos_codes': str(photos_codes),
                'korean_number': response['vehicleNo'],
                'dummy_id': dummy_id,
                'encar_diag': response['view']['encarDiagnosis'],
            }
            return detail_dict


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
            car_to_update = self.batch.get(encar_id=result['encar_id'])
            car_to_update.manufacturer = result['manufacturer']
            car_to_update.model = result['model']
            car_to_update.version = result['version']
            car_to_update.version_details = result['version_details']
            car_to_update.options = result['options']
            car_to_update.color = car_korean_dict['COLOR'].get(result['color'], result['color'])
            car_to_update.engine_capacity = result['engine_capacity']
            car_to_update.photos_codes = result['photos_codes']
            car_to_update.korean_number = result['korean_number']
            car_to_update.dummy_id = result['dummy_id']
            car_to_update.encar_diag = result['encar_diag']
            self.updated_batch.append(car_to_update)
        Car.objects.bulk_update(fields=['manufacturer', 
                                        'model', 
                                        'version', 
                                        'version_details', 
                                        'engine_capacity', 
                                        'color', 
                                        'options', 
                                        'korean_number', 
                                        'photos_codes', 
                                        'dummy_id', 
                                        'encar_diag'], objs=self.updated_batch)
        self.results = []




class DuplicateClearer():
    def __init__(self):
        self.unique_dummy_ids = self.get_unique_dummy_ids()
        self.all_cars = Car.objects.all().values('dummy_id', 'encar_id')
        self.encar_ids_to_delete = []


    def go_through_unique_dummy_ids(self):
        for dummy_id in self.unique_dummy_ids:
            duplicates = self.all_cars.filter(dummy_id=dummy_id).values('encar_id')
            if len(duplicates) != 1 and duplicates[0]['encar_id'] == dummy_id:
                self.encar_ids_to_delete.append(duplicates[0]['encar_id'])
            elif len(duplicates) != 1 and duplicates[1]['encar_id'] == dummy_id:
                self.encar_ids_to_delete.append(duplicates[1]['encar_id'])
        for i in range(math.ceil(len(self.encar_ids_to_delete) / 1000)):
            Car.objects.filter(encar_id__in=self.encar_ids_to_delete[i*1000:(i+1)*1000]).delete()
        Car.objects.filter(manufacturer__in=['Others', 'etc']).delete() #удаление неизвестных encar'u машин (others-others-others)
        Car.objects.filter(sell_type='Лизинг').delete()
        Car.objects.filter(sell_type='Аренда').delete()
        Car.objects.filter(engine_capacity__lt=900, fuel_type__in=['Бензин', 'Дизель', 'Бензин + Электро', 'Дизель + Электро']).delete()
        Car.objects.filter(engine_capacity__gt=9999).delete()
        Car.objects.filter(fuel_type='Прочее').delete()
        Car.objects.filter(fuel_type__in=["Газ (пропан-бутан) + Электро",
                                          'Прочее',
                                          'Водород',
                                          'Бензин + Метан',
                                          'Бензин + Газ (пропан-бутан)',
                                          'Газ (пропан-бутан)']).delete()



    def get_unique_dummy_ids(self):
        c = Car.objects.all().values('dummy_id')
        set1 = set()
        for elem in c:
            set1.add(elem['dummy_id'])
        print(len(set1))
        return list(set1)
        
    

    













class AsyncTruckParser():
    def __init__(self):
        self.batch_size = 100
        self.session = requests.Session()
        self.encar_api_url = 'https://api.encar.com/v1/readside/vehicle/'
        self.truck_count = Truck.objects.all().count()
        self.encar_ids = Truck.objects.all().values('encar_id')
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
        for i in range(math.ceil(self.truck_count/self.batch_size)):
            self.batch = Truck.objects.filter(encar_id__in=self.encar_ids[i*self.batch_size:(i+1)*self.batch_size], color=None, horse_power=None, options=None, engine_capacity=None)
            self.go_through_batch()
            self.save_to_db()


    def go_through_batch(self):
        list_api_urls = []
        for truck in self.batch:
            list_api_urls.append(f'{self.encar_api_url}{truck.encar_id}')
        print(f'Запуск {self.counter}')
        self.counter += 1
        self.results = asyncio.run(self.get_info(list_api_urls))
        
    

    async def fetch(self, session, url):
        async with session.get(url, timeout=10) as response:
            response = await response.json()
            photos_codes = list(map(lambda x: x['path'][-7:-4], response['photos']))
            detail_dict = {
                'encar_id': int(url.split('/')[-1]),
                'options': response['options']['standard'],
                'color': response['spec']['colorName'],
                'engine_capacity': response['spec']['displacement'],
                'photos_codes': str(photos_codes),
                # 'horse_power': response['spec']['horsePower'],
                'korean_number': response['vehicleNo']
            }
            return detail_dict


    async def get_info(self, batch):
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.session.cookies) as session:
            tasks = [self.fetch(session, url) for url in batch]
            results = await asyncio.gather(*tasks)
            return results
    

    def get_cookies(self):
        self.session.get("https://www.encar.com", headers=self.headers) 


    def save_to_db(self):
        self.updated_batch = []
        for result in self.results:
            truck_to_update = self.batch.get(encar_id=result['encar_id'])
            truck_to_update.options = result['options']
            truck_to_update.color = car_korean_dict['COLOR'].get(result['color'], result['color'])
            truck_to_update.engine_capacity = result['engine_capacity']
            truck_to_update.photos_codes = result['photos_codes']
            # truck_to_update.horse_power = result['horse_power'],
            truck_to_update.korean_number = result['korean_number']
            self.updated_batch.append(truck_to_update)
        Truck.objects.bulk_update(fields=['horse_power', 'engine_capacity', 'color', 'options', 'korean_number', 'photos_codes'], objs=self.updated_batch)
        self.results = []
