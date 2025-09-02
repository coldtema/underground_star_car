from .models import Car
import math
import requests
import time
from datetime import date
one_eur = 1614.69 #(kor w)



class RuPriceCalc:
    def __init__(self):
        self.currency_checker_url = 'https://www.cbr-xml-daily.ru/daily_json.js'
        self.currency_dict = dict()
        self.batch_size = 1000
        self.car_count = Car.objects.all().count()
        self.encar_ids = Car.objects.all().values('encar_id')
        self.headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
                    "Referer": "https://www.encar.com/",
                    "Accept": "application/json, text/plain, */*",
        }
        self.batch = []
        self.current_vechile = None
        self.current_vechile_age = 0
        self.current_vechile_ru_price = 0
        self.price_shift = 0.989


    def run(self):
        self.get_currency()
        self.batching_query()


    def get_currency(self):
        response = requests.get(self.currency_checker_url).json()
        self.currency_dict['krw/rub'] = response['Valute']['KRW']['Value']/response['Valute']['KRW']['Nominal']
        self.currency_dict['eur/rub'] = response['Valute']['EUR']['Value']/response['Valute']['EUR']['Nominal']
        self.currency_dict['usd/rub'] = response['Valute']['USD']['Value']/response['Valute']['USD']['Nominal']
        print(self.currency_dict)


    def fuel_type_dispatcher(self):
        if self.current_vechile.fuel_type == 'Электро':
            price_customs_duty = self.get_customs_duty_electro()
            excise_tax = self.get_excise_tax()
            recycling_fee = self.get_recycling_fee_electro()
            customs_clearance_fee = self.get_customs_clearance_fee()
            nds_tax = self.get_nds_tax(excise_tax, price_customs_duty)
            return self.get_final_price(price_customs_duty, excise_tax, customs_clearance_fee, nds_tax), recycling_fee
        elif self.current_vechile.fuel_type in ['Дизель', 'Бензин', 'Дизель + Электро', 'Бензин + Электро']:
            price_customs_duty = self.get_customs_duty_gasoline()
            recycling_fee = self.get_recycling_fee_gasoline()
            customs_clearance_fee = self.get_customs_clearance_fee()
            return self.get_final_price(price_customs_duty, customs_clearance_fee), recycling_fee
        return None


    def batching_query(self):
        '''Функция прохода через все батчи легковых машин'''
        for i in range(math.ceil(self.car_count/self.batch_size)):
            self.batch = Car.objects.filter(encar_id__in=self.encar_ids[i*self.batch_size:(i+1)*self.batch_size])
            self.go_through_batch()
            self.save_to_db()

    
    def go_through_batch(self):
        for car in self.batch:
            self.current_vechile = car
            car.customs_duty, car.recycling_fee = self.fuel_type_dispatcher()
            car.ru_price = self.current_vechile_ru_price


    def get_customs_duty_electro(self):
        self.current_vechile_ru_price = math.ceil(self.currency_dict['krw/rub'] * self.current_vechile.price * 10000 * self.price_shift)
        return math.ceil(self.current_vechile_ru_price * 0.15)



    def get_customs_duty_gasoline(self):
        self.current_vechile_ru_price = math.ceil(self.currency_dict['krw/rub'] * self.current_vechile.price * 10000 * self.price_shift)
        vechile_price_in_eur = math.ceil(self.current_vechile_ru_price/self.currency_dict['eur/rub'])
        # print(f'Цена в вонах: {self.current_vechile.price * 10000}')
        # print(f'Цена в рублях: {vechile_price_in_rub}')
        # print(f'Цена в евро: {vechile_price_in_eur}')
        self.current_vechile_age = ((date.today()-date(year=int(str(self.current_vechile.release_date)[:-2]), month=int(str(self.current_vechile.release_date)[-2:]), day=1)).days)//365
        # print(f'Возраст: {self.current_vechile_age}')
        # print(f'Объем двигателя: {self.current_vechile.engine_capacity}')
        if self.current_vechile_age < 3:
            for key, value in customs_duty_dict['LESS_3_YEARS'].items():
                if key[0] <= vechile_price_in_eur <= key[1]:
                    return math.ceil(max(vechile_price_in_eur * value[0], value[1]*self.current_vechile.engine_capacity) * self.currency_dict['eur/rub'])
        elif 3 <= self.current_vechile_age < 5:
            for key, value in customs_duty_dict['FROM_3_TO_5_YEARS'].items():
                if key[0] <= self.current_vechile.engine_capacity <= key[1]:
                    return math.ceil(value * self.current_vechile.engine_capacity * self.currency_dict['eur/rub'])
        elif 5 <= self.current_vechile_age:
            for key, value in customs_duty_dict['MORE_5_YEARS'].items():
                if key[0] <= self.current_vechile.engine_capacity <= key[1]:
                    return math.ceil(value * self.current_vechile.engine_capacity * self.currency_dict['eur/rub'])


    def get_excise_tax(self):
        current_vechile_engine_capacity = horsepower_dict.get(f'{self.current_vechile.manufacturer} {self.current_vechile.model} {self.current_vechile.version} {self.current_vechile.version_details} {self.current_vechile.model_year}', 0)
        if current_vechile_engine_capacity == 0:
            print(f'{self.current_vechile.manufacturer} {self.current_vechile.model} {self.current_vechile.version} {self.current_vechile.version_details} {self.current_vechile.model_year}', 'не нашлось мощности')
        for key, value in excise_tax_dict.items():
            if key[0] <= current_vechile_engine_capacity <= key[1]:
                return math.ceil(current_vechile_engine_capacity / 0.75 * value)


    def get_recycling_fee_electro(self):
        if 0 <= self.current_vechile_age <= 3:
            return recycling_fee_dict['ELECTRO_LESS_3_YEARS'] * 20000
        else:
            return recycling_fee_dict['ELECTRO_MORE_3_YEARS'] * 20000


    def get_recycling_fee_gasoline(self):
        if 0 <= self.current_vechile_age < 3:
             for key, value in recycling_fee_dict['GASOLINE_LESS_3_YEARS'].items():
                if key[0] <= self.current_vechile.engine_capacity <= key[1]:
                    return 20000 * value
        else:
            for key, value in recycling_fee_dict['GASOLINE_MORE_3_YEARS'].items():
                if key[0] <= self.current_vechile.engine_capacity <= key[1]:
                    return 20000 * value


    def get_customs_clearance_fee(self):
        for key, value in customs_clearance_fee_dict.items():
                if key[0] <= self.current_vechile_ru_price <= key[1]:
                    return value
                
    def get_nds_tax(self, excise_tax, price_customs_duty):
        return math.ceil((self.current_vechile_ru_price + excise_tax + price_customs_duty) * 0.20)


    def get_final_price(self, *args):
        return sum(args)


    def save_to_db(self):
        Car.objects.bulk_update(fields=['ru_price', 'recycling_fee', 'customs_duty'], objs=self.batch)
        self.batch = []





customs_duty_dict = {
    'LESS_3_YEARS':{
        (0, 8500): (0.54, 2.5), #(% from cost (in eur), but not less than eur/cm3)
        (8501, 16700): (0.48, 3.5),
        (16701, 42300): (0.48, 5.5),
        (42301, 84500): (0.48, 7.5),
        (84501, 169000): (0.48, 15),
        (169001, 100000000): (0.48, 20),
    },
    'FROM_3_TO_5_YEARS': {
        (0, 999): 1.5, #(eur/cm3)
        (1000, 1499): 1.7,
        (1500, 1799): 2.5,
        (1800, 2299): 2.7,
        (2300, 2999): 3.0,
        (3000, 100000): 3.6,
    },
    'MORE_5_YEARS': {
        (0, 999): 3.0,
        (1000, 1499): 3.2,
        (1500, 1799): 3.5,
        (1800, 2299): 4.8,
        (2300, 2999): 5.0,
        (3000, 100000): 5.7,
    }
}


customs_clearance_fee_dict = {
    (0, 200000): 775, #rub
    (200001, 450000): 1550,
    (450001, 1200000): 3100,
    (1200001, 2700000): 8530,
    (2700001, 4200000): 12000,
    (4200001, 5500000): 15500,
    (5500001, 7000000): 20000,
    (7000001, 8000000): 23000,
    (8000001, 9000000): 25000,
    (9000001, 10000000): 27000,
    (10000001, 1000000000): 30000,
}



excise_tax_dict = {
    (0, 67.4): 0, #rub/0,75kwt
    (67.5, 112.4): 60,
    (112.5, 149.9): 579,
    (150, 224.9): 948,
    (225, 299.9): 1617,
    (300, 374.9): 1673,
    (375, 100000): 1728,
}

recycling_fee_dict = { #*20000 rub
    'ELECTRO_LESS_3_YEARS': 0.17,
    'ELECTRO_MORE_3_YEARS': 0.26,
    'GASOLINE_LESS_3_YEARS':{
        (0, 1000): 0.17, 
        (1001, 2000): 0.17,
        (2001, 3000): 0.17,
        (3001, 3500): 107.67,
        (3501, 100000): 137.11,
    },
    'GASOLINE_MORE_3_YEARS': {
        (0, 1000): 0.26,
        (1001, 2000): 0.26,
        (2001, 3000): 0.26,
        (3001, 3500): 164.84,
        (3501, 100000): 180.24,
    },
}




horsepower_dict = {
    "Kia Soul EV None 2015": 27,
    "Mini Countryman ALL4 SE JCW None 2025": 14.9,  # PHEV
    "Jaguar I-PACE EV400 First Edition None 2019": 90,
    "Audi e-tron 55 Quattro None 2021": 95,
    "Audi Q4 e-tron 45 Premium None 2025": 82,
    "Peugeot 2008 EV GT None 2021": 50,
    "Mercedes-Benz EQA EQA250 Progressive None 2025": 66.5,
    "BMW iX1 xDrive 30 xLine None 2023": 64.7,
    "BMW iX1 xDrive 30 xLine None 2024": 64.7,
    "Mercedes-Benz EQE EQE500 4MATIC None 2024": 90.6,
    "Genesis G80 e-AWD None 2022": 87.2,
    "Kia EV3 Long Range 2WD GT-Line 2025": 81.4,
    "Hyundai Ioniq5 Standard AWD Prestige 2022": 58,
    "Volvo XC40 Twin Ultimate None 2022": 78,
    "Mercedes-Benz EQA EQA250 None 2023": 66.5,
    "Renault-KoreaSamsung SM3 RE None 2020": 35.9,
    "Tesla Model Y Long Range None 2024": 75,
    "Tesla Model S 90D None 2017": 90,
    "Hyundai Ioniq5 Long Range Exclusive 2025": 77.4,
    "Peugeot 2008 EV GT None 2023": 54,
    "Hyundai Ioniq5 Standard Exclusive 2022": 58,
    "Hyundai Ioniq9 Performance Type AWD 6-Seater Calligraphy 2025": 100,  # ожидаемо
    "Hyundai Ioniq5 Standard Commercial 2022": 58,
    "Volvo EX30 Ultra None 2025": 69,
    "Audi Q8 e-tron 50 Quattro None 2024": 95,
    "Porsche Taycan Turbo S None 2021": 93.4,
    "Kia RAY EV None 2014": 16.4,
    "Kia Niro Noblesse None 2021": 64.8,
    "Hyundai Ioniq5 Standard Commercial 2023": 58,
    "BMW i7 xDrive 60 Design Pure Excellence None 2023": 105.7,
    "Tesla Model 3 Performance None 2022": 82,
    "Hyundai Ioniq5 Long Range AWD Exclusive 2024": 77.4,
    "Kia Niro Noblesse None 2020": 64,
    "BMW i7 xDrive 60 M sport None 2024": 105.7,
    "Kia EV3 Standard 2WD Earth 2025": 58,
    "Audi e-tron 55 Quattro Sportback None 2022": 95,
    "Audi e-tron S None 2022": 95,
    "Mercedes-Benz EQE EQE350+ None 2024": 90.6,
    "BMW i3 SOL+ None 2016": 33,
    "BMW iX1 xDrive 30 M Sport None 2024": 64.7,
    "Kia EV6 Standard 4WD Air 2022": 58,
    "Mini Cooper SE Electric 3rd 2022": 32.6,
    "Porsche Taycan GTS None 2023": 93.4,
    "Kia EV6 Long Range 4WD Air 2022": 77.4,
    "Audi Q4 e-tron 40 Premium Sportback None 2022": 82,
    "Kia Niro Noblesse None 2022": 64.8,
    "Porsche Taycan 4S None 2022": 93.4,
    "Porsche Taycan Turbo None 2025": 93.4,
    "Kia EV9 Long Range 4WD GT Line 2024": 99.8,
    "Kia EV9 Long Range 4WD GT Line 2026": 99.8,
    "BMW iX xDrive50 Sports Plus None 2025": 111.5,
    "Kia EV6 Long Range 4WD GT Line 2023": 77.4,
    "BMW i3 LUX None 2020": 42.2,
    "Hyundai Ioniq5 Long range Exclusive 2023": 77.4,
    "ChevroletGMDaewoo Bolt EV EV Premier None 2023": 66,
    "Kia Niro Air None 2024": 64.8,
    "Tesla Model 3 Long Range None 2019": 75,
    "Tesla Model X Long Range None 2025": 100,
    "Lexus UX 2WD None 2022": 54.3,
    "Kia EV3 Long Range 2WD AIr 2026": 81.4,
    "Hyundai Ioniq N None 2020": 38.3,  # спортивная версия PHEV
    'Hyundai Ioniq I None 2018': 30.5,
    "Kia Niro Earth None 2024": 64.8,
    "BMW i4 M50 None 2024": 83.9,
    "Kia EV9 Long Range 4WD Air 2024": 99.8,
    "Tesla Model Y Long Range None 2023": 75,
    "ChevroletGMDaewoo Bolt EV EV Premier None 2022": 66,
    "Kia EV9 Long Range Earth 2024": 99.8,
    "BMW i5 eDrive 40 M Sport None 2025": 81.2,
    "Peugeot 2008 EV GT Line None 2020": 50,
    "Kia EV3 Standard 2WD GT-Line 2025": 58,
    "Nissan Leaf EV SL None 2019": 62,
    "Kia EV6 Long Range Earth 2022": 77.4,
    "Audi Q8 e-tron 55 Quattro Premium Sportback None 2024": 114,
    "Mercedes-Benz EQS EQS450+ None 2023": 107.8,
    "Mercedes-Benz EQS EQS53 AMG 4MATIC+ None 2022": 107.8,
    "Volvo EX30 Ultra None 2024": 69,
    "Porsche Taycan 4S None 2025": 93.4,
    "Kia RAY Light None 2024": 35.2,
    "Mercedes-Benz EQA EQA250 AMG Package None 2022": 66.5,
    "Mercedes-Benz EQA EQA250 AMG Package None 2021": 66.5,
    "KG_Mobility_Ssangyong Torres E7 None 2024": 73.4,
    "Volvo C40 Twin Ultimate None 2022": 78,
    "Kia Niro Earth None 2025": 64.8,
    "Hyundai Ioniq5 Long range Prestige 2022": 77.4,
    "Audi Q4 e-tron 40 Premium None 2022": 82,
    "Audi Q4 e-tron 40 Premium None 2025": 82,
    "BMW i4 M50 None 2022": 83.9,
    "BMW i7 xDrive 60 Design Pure Excellence None 2024": 105.7,
    "Mercedes-Benz EQS EQS450 4MATIC Launch Edition None 2024": 107.8,
    "Hyundai Ioniq6 Long Range Exclusive 2023": 77.4,
    "Hyundai Kona Premium None 2019": 64,
    "Audi Q6 e-tron Performance None 2025": 100,
    "Tesla Model Y RWD None 2023": 60,
    "Hyundai ST1 Cargo Premium 2025": 74,  # ожидаемо
    "Kia EV6 Long Range 2WD GT Line 2025": 77.4,
    "Tesla Model S Performance None 2020": 100,
    "Kia EV9 Long Range 4WD GT Line 2023": 99.8,
    "Kia RAY Van 2-Seater AIr 2024": 35.2,
    "Hyundai Ioniq5 Long range Exclusive 2024": 77.4,
    "BMW i4 eDrive40 M Sports None 2022": 83.9,
    "Mercedes-Benz G-Class G580 EQ Technology None 2025": 116,
    "Polestar Polestar 2 Longrange Dualmotor None 2023": 78,
    "Renault-KoreaSamsung SM3 RE None 2016": 22,
    "Volvo XC40 Twin None 2024": 78,
    "Hyundai Ioniq9 Cruise Type AWD 6-Seater Calligraphy 2025": 100,
    "Kia EV6 GT 4WD None 2025": 77.4,
    "Mercedes-Benz EQS EQS450 4MATIC None 2023": 107.8,
    "Kia EV6 Standard Air 2023": 58,
    "Mercedes-Benz EQE EQE350+ None 2023": 90.6,
    "Audi RS e-tron GT GT RS None 2022": 93.4,
    "Audi RS e-tron GT GT RS None 2023": 93.4,
    "Ford Mustang AWD None 2018": 10,  # PHEV EcoBoost ~10 кВт·ч
    "Tesla Model Y RWD None 2024": 60,
    "Hyundai Ioniq5 Long Range Prestige 2023": 77.4,
    "Others Others Others EV None 2022": 0,
    "Polestar Polestar 2 Longrange Singlemotor None 2022": 78,
    "Polestar Polestar 4 Long Range Single Moter None 2025": 100,
    "Porsche Macan Base 4 None 2025": 95,
    "Mercedes-Benz EQS EQS450 4MATIC Launch Edition None 2023": 107.8,
    "Mercedes-Benz EQA EQA250 None 2024": 66.5,
    "Tesla Model X 100D None 2018": 100,
    "Porsche Taycan 4S None 2024": 93.4,
    "Kia Niro Prestige None 2022": 64.8,
    "Hyundai Kona Modren None 2021": 64,
    "Kia Niro Prestige None 2019": 64,
    "ChevroletGMDaewoo Bolt EV EV None 2017": 60,
    "Porsche Taycan Turbo S None 2025": 93.4,
    "Porsche Taycan Turbo S None 2022": 93.4,
    "Kia EV9 Long Range Air 2024": 99.8,
    "Kia Soul Noblesse None 2021": 64,
    "Others Others Others EV None 2019": 0,
    "Kia Soul Prestige None 2019": 64,
    "BMW i3 SOL+ None 2015": 22,
    "Kia Soul EV None 2016": 27,
    "Others Others Others EV None 2020": 0,
    "Hyundai Kona Premium None 2020": 64,
    "Tesla Model S AWD None 2023": 100,
    "Mercedes-Benz EQS Maybach EQS680 4MATIC None 2025": 118,
    "Mercedes-Benz EQB EQB300 4MATIC AMG Line None 2023": 66.5,
    "Hyundai Kona Long Range Premium 2025": 77,
    "Hyundai Ioniq5 Long Range AWD Prestige 2024": 77.4,
    "Porsche Taycan 4 Cross Turismo None 2022": 93.4,
    "Mercedes-Benz G-Class G580 EQ Edition 1 None 2025": 116,
    "Volvo XC40 Twin Ultimate None 2024": 78,
    "Kia EV6 Long Range 4WD Light 2022": 77.4,
    'Kia EV6 Long Range 4WD Light 2023': 77.4,
    'Kia EV6 Long Range 4WD Light 2024': 77.4,
    "Genesis GV70 e-AWD None 2022": 77.4,
    "Hyundai Ioniq Q None 2020": 38.3,  # PHEV
    "Renault-KoreaSamsung Zoe Intens Eco None 2021": 52,
    "Tesla Cybertruck Cyberbeast None 2024": 123,
    "BMW i5 M60 xDrive None 2024": 81.2,
    "BMW iX1 xDrive 30 M Sport None 2023": 64.7,
    "Tesla Model 3 Long Range None 2020": 75,
    "BMW i3 SOL+ None 2018": 33,
    "Kia EV6 Long Range 4WD Earth 2022": 77.4,
    "DFSK C35 EV  4-Seater None 2023": 41.9,
    "DFSK C35 EV  4-Seater None 2022": 41.9,
    "Mini Cooper SE Electric 3rd 2023": 32.6,
    "BMW i3 LUX None 2015": 22,
    "Tesla Model 3 Standard Range Plue None 2021": 55,
    "Hyundai Ioniq N None 2019": 38.3,  # PHEV
    "Mini Cooper SE Favoured None 2024": 33,
    "ChevroletGMDaewoo 볼트 EUV Redline None 2023": 65,
    "Kia Niro Air (Taxi Trim) None 2024": 64.8,
    "DFSK C35 EV 2 Seater Van None 2023": 41.9,
    "Hyundai Ioniq Q None 2019": 38.3,
    "Mercedes-Benz EQB EQB300 4MATIC Electric Art None 2024": 66.5,
    "Mercedes-Benz EQB EQB300 4MATIC Progressive None 2025": 66.5,
    "Hyundai Ioniq5 Long Range AWD Exclusive 2022": 77.4,
    "Renault-KoreaSamsung SM3 RE None 2019": 35.9,
    "BMW i4 eDrive40 M Sports Pro None 2023": 83.9,
    "Hyundai Ioniq5 Standard Prestige 2022": 58,
    "Cadillac Lyriq Sport None 2024": 102,
    "Renault-KoreaSamsung Twizy Intens(2-seater) None 2019": 6.1,
    "BMW i4 eDrive40 M Sports None 2025": 83.9,
    "Renault-KoreaSamsung Twizy Cargo(1-seater+Trunk) None 2019": 6.1,
    "Kia EV6 Long Range Earth 2023": 77.4,
    "Audi Q4 e-tron 40 Premium Sportback None 2024": 82,
    "Kia EV6 Long Range Earth 2024": 77.4,
    "Renault-KoreaSamsung Twizy Intens(2-seater) None 2018": 6.1,
    "Mercedes-Benz EQA EQA250 AMG Line None 2025": 66.5,
    "Nissan Leaf EV SL None 2015": 24,
    "Polestar Polestar 2 Longrange Singlemotor None 2023": 82,
    "Hyundai Ioniq6 Long Range AWD Exclusive + 2023": 77.4,
    "Hyundai Ioniq6 Long Range AWD Exclusive 2025": 77.4,
    "Kia EV6 Standard Earth 2022": 58,
    "BMW iX xDrive50 Sports Plus None 2024": 111.5,
    "BMW i7 xDrive 60 Design Pure Excellence Individual None 2023": 105.7,
    "Jaguar I-PACE EV400 HSE None 2019": 90,
    "DFSK C35 EV 2 Seater Van None 2022": 41.9,
    "Porsche Taycan Turbo S None 2023": 93.4,
    "Mercedes-Benz EQB EQB300 4MATIC AMG Line None 2024": 66.5,
    "Genesis GV60 Performance AWD None 2023": 77.4,
    "ChevroletGMDaewoo Bolt EV EV Premier None 2021": 66,
    "Kia RAY Air None 2025": 35.2,
    "Hyundai Ioniq5 Long range Commercial 2022": 58,
    "Audi Q4 e-tron 45 None 2025": 82,
    "Hyundai ST1 Cargo Freezer Container Premium 2025": 74,
    "Mercedes-Benz EQC EQC400 4MATIC None 2021": 80,
    "Mercedes-Benz EQA EQA250 None 2021": 66.5,
    "Hyundai Casper Premium None 2025": 39.2,
    "Genesis GV60 Standard AWD None 2023": 77.4,
    "Mini Cooper SE Classic 3rd 2022": 32.6,
    "Mini Cooper SE Classic 3rd 2023": 32.6,
    'Mini Cooper SE Classic None 2024': 32.6,
    'Lotus Eletre R None 2025': 111.9,
    'Mercedes-Benz EQC EQC400 4MATIC Premium None 2020': 300,
    "Audi e-tron 50 Quattro Sportback None 2022": 71,
    "Hyundai Ioniq6 Long Range AWD Prestige 2025": 77.4,
    "Mercedes-Benz EQB EQB300 4MATIC None 2024": 66.5,
    "ChevroletGMDaewoo 볼트 EUV Premier None 2023": 65,
    "Hyundai Ioniq5 Long Range AWD N Line 2025": 77.4,
    "Hyundai Casper Inspiration None 2025": 39.2,
    "Porsche Taycan 4S None 2021": 93.4,
    "Fiat 500 EV None 2024": 42,
    "Tesla Model 3 RWD None 2024": 60,
    "Renault-KoreaSamsung SM3 SE None 2019": 35.9,
    "Kia EV3 Long Range 2WD Earth 2025": 81.4,
    "Mini Cooper Resolute Edition 3rd 2023": 32.6,
    "Renault-KoreaSamsung SM3 RE None 2018": 35.9,
    "Kia Soul EV None 2017": 30,
    "Porsche Taycan Turbo Cross Turismo None 2022": 93.4,
    "BMW i4 eDrive40 M Sports Pro None 2022": 83.9,
    "BMW iX1 xDrive 30 M Sport None 2025": 64.7,
    "Hyundai Ioniq N None 2018": 8.9,   # PHEV
    "Hyundai Ioniq6 Long Range Exclusive + 2023": 77.4,
    "Tesla Model S 100D None 2017": 100,
    "Mercedes-Benz EQE EQE53 AMG 4MATIC+ None 2024": 90.6,
    "BMW i5 eDrive 40 None 2024": 81.2,
    "Nissan Leaf EV None 2016": 30,
    "Kia EV9 Long Range 4WD Earth 2024": 99.8,
    "BMW i7 eDrive 50 M Sport Limited None 2024": 101.7,
    "BMW i4 M50 None 2023": 83.9,
    "BMW iX2 eDrive 20 M Sport None 2024": 64.7,
    "Tesla Model X Performance None 2019": 100,
    "Tesla Model 3 Long Range None 2022": 75,
    "Kia Soul EV None 2018": 30,
    "Renault-KoreaSamsung Twizy Life(2-Seater) None 2019": 6.1,
    "Tesla Model 3 Performance None 2021": 75,
    "Hyundai Ioniq6 Long Range Prestige 2023": 77.4,
    "Tesla Model 3 Long Range None 2025": 75,
    "Tesla Model S 75D None 2019": 75,
    "Audi Q4 e-tron 40 Sportback None 2022": 82,
    "Kia EV6 Long Range GT Line 2023": 77.4,
    "Mercedes-Benz EQC EQC400 4MATIC None 2020": 80,
    "Polestar Polestar 4 Long Range Duel Moter None 2025": 100,
    "Jaguar I-PACE EV400 HSE None 2020": 90,
    "Tesla Model Y Standard Range None 2021": 55,
    "Tesla Model 3 Long Range None 2021": 75,
    "Mercedes-Benz EQA EQA250 AMG Line None 2023": 66.5,
    "Hyundai ST1 Cargo Freezer Container Smart 2025": 74,
    "Mercedes-Benz EQS EQS350 None 2022": 90.6,
    "BMW iX xDrive50 Sports Plus None 2023": 111.5,
    "Fiat 500 EV None 2017": 24,
    "Audi Q4 e-tron 40 Sportback None 2023": 82,
    "Porsche Taycan Base None 2025": 83.6,
    "Porsche Taycan Base None 2022": 79.2,
    "Mini Cooper SE Electric 3rd 2024": 33,
    "Mercedes-Benz EQS EQS580 4MATIC Launch Edition None 2023": 107.8,
    'Mercedes-Benz EQS EQS580 4MATIC Launch Edition None 2024': 107.8,
    "Peugeot 208 GT None 2021": 50,
    "Porsche Taycan Base None 2024": 83.6,
    "Tesla Model 3 RWD None 2022": 55,
    "Peugeot 2008 EV GT None 2022": 50,
    "Peugeot 2008 EV GT None 2025": 54,
    "Volvo C40 Twin Ultimate None 2023": 78,
    "Kia EV3 Standard 2WD Air 2025": 58.3,
    "Hyundai Ioniq5 Standard E-Value+ 2025": 58,
    "ChevroletGMDaewoo Bolt EV EV LT DLX None 2019": 60,
    "Porsche Taycan 4 Cross Turismo None 2023": 93.4,
    "Tesla Model 3 Long Range None 2024": 75,
    "Porsche Taycan 4 Cross Turismo None 2025": 95,
    "Tesla Model X 100D None 2019": 100,
    "Genesis G80 e-AWD None 2023": 87.2,
    "Kia Niro Taxi None 2019": 64,
    "Mercedes-Benz EQA EQA250 AMG Package None 2024": 66.5,
    "Audi e-tron 50 Quattro None 2021": 71,
    "Hyundai Ioniq5 Long range Exclusive 2022": 77.4,
    "Others Others Others EV None 2018": 0,
    "Kia RAY EV None 2013": 16.4,
    "Renault-KoreaSamsung SM3 SE Plus None 2014": 22,
    "Hyundai Kona Modren None 2020": 64,
    "Porsche Macan 4S None 2025": 95,
    "Tesla Model S 75D None 2017": 75,
    "Tesla Model 3 Standard Range Plue None 2019": 50,
    "Kia Niro Air (Taxi Trim) None 2023": 64.8,
    "Tesla Model X Long Range None 2020": 100,
    "Kia EV6 GT 4WD None 2024": 77.4,
    "Hyundai Ioniq6 Long Range Prestige 2024": 77.4,
    "Kia RAY Van 2-Seater Light 2024": 35.2,
    "Nissan Leaf EV None 2015": 24,
    "Renault-KoreaSamsung SM3 RE None 2014": 22,
    "Hyundai Ioniq N None 2017": 8.9,  # PHEV
    "Kia EV6 Long Range Air 2024": 77.4,
    "Genesis GV60 Standard AWD None 2025": 77.4,
    "Hyundai Ioniq Q None 2017": 8.9,  # PHEV
    "Kia EV6 Long Range 4WD Air 2023": 77.4,
    "Mini Countryman ALL4 SE Favoured None 2025": 14,  # PHEV ~14 кВт·ч
    "Hyundai Ioniq6 Long Range AWD Exclusive 2023": 77.4,
    "Citroen-DS DS3 E-Tense Grand Chic None 2022": 50,
    'Citroen-DS DS3 E-Tense Grand Chic None 2021': 50,
    "Tesla Cybertruck AWD None 2024": 123,
    "Mercedes-Benz EQS Maybach EQS680 4MATIC None 2024": 118,
    "Audi Q4 e-tron 40 None 2023": 82,
    "Hyundai Ioniq5 Long range Prestige 2023": 77.4,
    "Jeep Avenger Altitude None 2024": 54,
    "Hyundai Ioniq5 Long Range AWD Commercial Long Range Package 2023": 77.4,
    "Peugeot 2008 EV GT Line None 2021": 50,
    "ChevroletGMDaewoo Bolt EV EV Premier None 2017": 60,
    "Kia EV6 Long Range 4WD GT Line 2024": 77.4,
    "Kia EV6 Long Range Air 2023": 77.4,
    "Kia Niro Noblesse None 2019": 64,
    "Audi Q4 e-tron 40 Premium Sportback None 2023": 82,
    "BMW iX3 M Sports None 2022": 80,
    "Mercedes-Benz EQE EQE500 4MATIC None 2023": 90.6,
    "Mercedes-Benz EQA EQA250 AMG Package Plus None 2021": 66.5,
    "Tesla Model S 100D None 2019": 100,
    "Polestar Polestar 2 Standard Singlemotor None 2023": 69,
    "Porsche Taycan GTS None 2024": 93.4,
    "Hyundai Kona Long Range Inspiration 2023": 64.8,
    "Hyundai Kona Long Range Inspiration 2025": 64.8,
    "Smart Fortwo ED(electric drive) None 2016": 17.6,
    "Kia RAY Air None 2024": 35.2,
    "KG_Mobility_Ssangyong KORANDO E5 None 2022": 61.5,
    "Hyundai Kona Long Range Premium 2023": 64.8,
    "Mini Cooper Resolute Edition 3rd 2024": 32.6,
    "Volvo XC40 Twin Ultimate None 2023": 78,
    "Hyundai Ioniq5 Long Range Commercial 2025": 77.4,
    "BMW iX xDrive40 First Edition None 2022": 71,
    "Porsche Taycan 4S Cross Turismo None 2024": 93.4,
    "ChevroletGMDaewoo Bolt EV EV LT DLX None 2018": 60,
    "Genesis GV60 Standard None 2023": 77.4,
    "Tesla Model Y Long Range None 2021": 75,
    "Hyundai Ioniq5 Long Range AWD Prestige 2023": 77.4,
    "Hyundai Ioniq5 Long Range Prestige 2025": 77.4,
    "Tesla Model Y Performance None 2021": 75,
    "Audi Q4 e-tron 40 Premium None 2024": 82,
    "Tesla Model Y Long Range None 2022": 75,
    "Hyundai Ioniq5 Long Range AWD Commercial Long Range Package 2022": 77.4,
    "Renault-KoreaSamsung Twizy Life(2-Seater) None 2020": 6.1,
    "Renault-KoreaSamsung SM3 RE None 2015": 22,
    "BMW i7 xDrive 60 M sport None 2025": 101.7,
    "Peugeot 208 GT Line None 2022": 50,
    "Kia Niro Prestige None 2021": 64.8,
    "Tesla Model Y RWD None 2025": 60,
    "Hyundai Ioniq6 Long Range Exclusive 2022": 77.4,
    "Tesla Model Y Long Range None 2025": 75,
    "BMW i5 eDrive 40 M Sport None 2024": 81.2,
    "Kia EV6 Long Range 4WD Earth 2025": 77.4,
    "Mini Aceman SE Favoured None 2025": 54,
    "Mercedes-Benz EQS EQS53 AMG 4MATIC+ None 2024": 107.8,
    "Mercedes-Benz EQB EQB300 4MATIC AMG Line None 2025": 70.5,
    "Kia EV6 Standard Air 2022": 58,
    "Jaguar I-PACE EV400 SE None 2019": 90,
    "BMW i5 eDrive 40 M Sport Pro None 2024": 81.2,
    "Hyundai Ioniq5 Long Range AWD Prestige 2022": 77.4,
    "Hyundai Ioniq Q None 2018": 8.9,  # PHEV
    "ChevroletGMDaewoo 볼트 EUV Premier None 2022": 65,
    "Hyundai Kona Long Range Inspiration 2024": 64.8,
    "Kia EV6 Long Range 4WD Air 2024": 77.4,
    "BMW i7 eDrive 50 M Sport None 2024": 101.7,
    "Kia EV6 Long Range 4WD Earth 2024": 77.4,
    "BMW i7 M70 xDrive None 2024": 101.7,
    "BMW i4 eDrive40 M Sports Pro None 2024": 83.9,
    "Mercedes-Benz EQA EQA250 Electric Art None 2024": 66.5,
    "Mercedes-Benz EQA EQA250 Electric Art None 2023": 66.5,
    "Porsche Taycan 4S Cross Turismo None 2023": 93.4,
    "Mercedes-Benz EQS EQS450 4MATIC None 2024": 107.8,
    "Mini Cooper Gen ZE Edition 3rd 2022": 32.6,
    "Kia EV6 Long Range Air 2022": 77.4,
    "Hyundai Ioniq5 Long range Commercial Long Range Package 2023": 77.4,
    "Hyundai Ioniq5 Long range Commercial Long Range Package 2022": 77.4,
    "Audi Q4 e-tron 45 Sportback None 2025": 86,
    "BMW iX xDriveM60 None 2024": 111.5,
    "Tesla Model 3 Performance None 2020": 75,
    "GMC Hummer EV e4WD None 2024": 212,
    "Porsche Taycan Turbo Cross Turismo None 2023": 93.4,
    "ChevroletGMDaewoo Bolt EV EV LT None 2019": 60,
    "ChevroletGMDaewoo Bolt EV EV Premier None 2018": 60,
    "Renault-KoreaSamsung SM3 RE None 2017": 35.9,
    "Tesla Model X AWD None 2024": 100,
    "Porsche Taycan GTS None 2022": 93.4,
    "BMW i4 eDrive40 M Sports None 2024": 83.9,
    "Volvo C40 Twin Ultimate None 2024": 78,
    "Kia Niro Air None 2023": 64.8,
    "BMW iX3 M Sports None 2024": 80,
    "BMW i3 SOL+ None 2019": 42.2,
    "Kia RAY EV None 2016": 16.4,
    "Porsche Taycan 4S Cross Turismo None 2022": 93.4,
    "Tesla Model Y Performance None 2022": 75,
    "Kia RAY Van 1-Seater AIr 2025": 35.2,
    "BMW i4 M50 Pro None 2022": 83.9,
    "Mercedes-Benz EQS EQS580 4MATIC None 2023": 107.8,
    "BMW iX xDrive40 Sport Plus None 2022": 71,
    "Genesis G80 e-AWD None 2024": 87.2,
    "BMW i4 M50 Pro None 2024": 83.9,
    "Hyundai Ioniq5 N None 2024": 84,
    "Mercedes-Benz EQA EQA250 None 2022": 66.5,
    "Mercedes-Benz EQA EQA250 AMG Package Plus None 2022": 66.5,
    "Audi e-tron GT GT quattro Premium None 2022": 93.4,
    'Audi e-tron GT GT quattro None 2022': 93.4,
    "Peugeot 2008 EV Allure None 2023": 50,
    "Tesla Model X Performance None 2020": 100,
    "Kia EV3 Long Range 2WD AIr 2025": 81.4,
    "Peugeot 208 Allure None 2022": 50,
    "Kia Soul Prestige None 2021": 64,
    "ChevroletGMDaewoo Bolt EV EV LT DLX None 2020": 66,
    "Volkswagen ID.4 Pro None 2023": 82,
    'Volkswagen ID.4 Pro None 2025': 82,
    "Hyundai Kona Standard Premium 2023": 48.6,
    "ChevroletGMDaewoo Bolt EV EV LT DLX None 2021": 66,
    "Mercedes-Benz EQB EQB300 4MATIC None 2022": 70.5,
    "Mercedes-Benz EQE EQE350+ None 2022": 90.6,
    "Tesla Model 3 Standard Range Plue None 2022": 60,
    "BMW iX xDrive50 Sports Plus None 2022": 111.5,
    "Renault-KoreaSamsung SM3 SE None 2016": 22,
    "Hyundai Ioniq6 Long Range AWD Prestige 2023": 77.4,
    "Hyundai Ioniq6 Long Range AWD Prestige 2024": 77.4,
    "Others Others Others EV None 2021": 0,  # уточнить модель
    "Audi Q8 e-tron 55 Quattro Sportback None 2024": 114,
    "Smart Fortwo EQ None 2019": 17.6,
    "Smart Fortwo EQ None 2018": 17.6,
    "Porsche Taycan Base None 2023": 79.2,
    "Kia Niro Light (Taxi Trim) None 2023": 64.8,
    "Kia EV6 Long Range Light 2022": 77.4,
    "Renault-KoreaSamsung Twizy Cargo(1-seater+Trunk) None 2020": 6.1,
    "Hyundai Ioniq5 Long range Prestige 2024": 77.4,
    "Tesla Model X Plaid None 2023": 100,
    "Kia Soul Noblesse None 2019": 64,
    "Mercedes-Benz EQS EQS450+ AMG Line None 2022": 107.8,
    "Mercedes-Benz EQA EQA250 AMG Line None 2024": 66.5,
    "BMW iX2 eDrive 20 M Sport None 2025": 64.8,
    "Renault-KoreaSamsung Zoe Intens None 2021": 52,
    "Kia EV6 Long Range 4WD GT Line 2022": 77.4,
    "Mercedes-Benz EQS EQS53 AMG 4MATIC+ None 2023": 107.8,
    "Genesis GV60 Standard AWD None 2022": 77.4,
    "BMW i3 LUX None 2016": 22,
    "Others Others Others EV None 2023": 0,  # уточнить модель
    "Kia EV6 Long Range 4WD GT Line 2025": 77.4,
    "Rolls-Royce Spectre Coupe None 2024": 102,
    "Tesla Model X AWD None 2023": 100,
    "BMW i4 eDrive40 Individual None 2024": 83.9,
    "Volkswagen ID.4 Pro None 2022": 82,
    "Kia Niro Prestige None 2020": 64,
    "BMW i7 xDrive 60 M sport None 2023": 101.7,
    "Kia EV6 Long Range 4WD Earth 2023": 77.4,
    "Hyundai Kona Modren None 2019": 64,
    "Porsche Taycan Turbo None 2022": 93.4,
    "Mercedes-Benz EQA EQA250 AMG Package None 2025": 66.5,
    "Tesla Model S Long Range None 2020": 100,
    "Genesis GV60 Performance AWD None 2022": 77.4,
    "Tesla Model S Plaid None 2023": 100,
    "Mercedes-Benz EQE EQE350 4MATIC None 2023": 90.6,
    "Audi Q4 e-tron 40 Premium None 2023": 82,
    "Hyundai Ioniq6 Standard Exclusive 2023": 53,
    "Mercedes-Benz EQS EQS450+ None 2024": 107.8,
    "Nissan Leaf EV S None 2019": 40,
    "Hyundai Ioniq5 Long Range AWD Prestige 2025": 77.4,
    "BMW i4 M50 Pro None 2023": 83.9,
    "ChevroletGMDaewoo Bolt EV EV Premier None 2020": 66,
    "Kia EV6 Long Range GT Line 2022": 77.4,
    "Peugeot 208 GT None 2022": 50,
    "BYD Atto 3 Plus None 2025": 60.5,
    "BMW i3 SOL+ None 2020": 42.2,
    "Tesla Model 3 RWD None 2025": 60,
    "Mercedes-Benz EQB EQB300 4MATIC None 2023": 70.5,
    "Porsche Taycan Turbo S None 2024": 93.4,
    "Kia EV6 Long Range 2WD Earth 2025": 77.4,
    "Hyundai Ioniq6 Long Range E-Lite 2023": 77.4,
    "Tesla Model 3 Performance None 2024": 75,
    "BMW i3 SOL None 2015": 18.8,
    "Porsche Macan Turbo None 2025": 95,
    "KG_Mobility_Ssangyong Torres E7 None 2025": 73.4,
    "Audi e-tron 55 Quattro Sportback None 2021": 95,
    "Audi Q8 e-tron 55 Quattro None 2024": 114,
    "Audi e-tron GT GT quattro Premium None 2023": 93.4,
    "Porsche Taycan Turbo None 2021": 93.4,
    "Genesis GV60 Standard None 2025": 77.4,
    "Porsche Taycan Base None 2021": 79.2,
    "Tesla Model X Long Range None 2023": 100,
    "Hyundai Ioniq9 Cruise Type 2WD 6-Seater Prestige 2025": 100,  # новый, ориентировочно
    "Hyundai Ioniq6 Long Range Prestige 2025": 77.4,
    "Porsche Taycan Turbo Cross Turismo None 2024": 93.4,
    "Audi e-tron 55 Quattro None 2022": 95,
    "Citroen-DS DS3 E-Tense Grand Chic None 2023": 50,
    "BMW i3 LUX None 2017": 33,
    "Audi e-tron 55 Quattro None 2020": 95,
    "BMW i4 M50 Pro Special Edition None 2024": 83.9,
    "Genesis GV60 Standard None 2022": 77.4,
    "ChevroletGMDaewoo Bolt EV EV Premier None 2019": 60,
    "Kia EV6 GT 4WD None 2023": 77.4,
    "Mercedes-Benz EQE EQE53 AMG 4MATIC+ None 2023": 90.6,
    "Polestar Polestar 2 Longrange Dualmotor None 2022": 78,
    "Hyundai Ioniq5 Long Range AWD Exclusive 2023": 77.4,
    "Mercedes-Benz EQE EQE350 4MATIC None 2024": 90.6,
    "Lexus RZ Luxury None 2023": 71.4,
    "BMW iX3 M Sports None 2023": 80,
    "Kia RAY EV None 2017": 16.4,
    "Tesla Model 3 Standard Range Plue None 2020": 50,
    "Kia Niro Earth None 2023": 64.8,
    "Tesla Model X Long Range None 2019": 100,
    "Mercedes-Benz EQE EQE300 None 2023": 89,
    "Kia EV6 Standard Earth 2024": 58,
    "Kia EV6 Standard Earth 2023": 58,
    "Hyundai Kona Standard Premium 2025": 48.6,
}