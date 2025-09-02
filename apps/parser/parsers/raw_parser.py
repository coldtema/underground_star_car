import requests
import math
from ..models import Car, Truck

diagnosis = 'https://api.encar.com/v1/readside/diagnosis/vehicle/40286929'

car_info = 'https://api.encar.com/v1/readside/vehicle/39475708'

photos = 'https://ci.encar.com/carpicture/carpicture03/pic4003/40034021_001.jpg?impolicy=heightRate&rh=696&cw=1160&ch=696&cg=Center&wtmk=https://ci.encar.com/wt_mark/w_mark_04.png'


class CarParser():
    def __init__(self):
        self.current_mileage = 0
        self.current_page = 0
        self.url_dict = {
            'electro_url': ['https://api.encar.com/search/car/list/premium?count=True&q=(And.Hidden.N._.CarType.A._.GreenType.Y._.(Or.Separation.A._.Separation.B.)_.Mileage.range(', '0', '..', '10000', ').)&sr=%7CModifiedDate%7C', '0', '%7C1000'],
            'import_url': ['https://api.encar.com/search/car/list/premium?count=True&q=(And.Hidden.N._.CarType.N._.(Or.Separation.A._.Separation.F._.Separation.B.)_.SellType.%EC%9D%BC%EB%B0%98._.Mileage.range(', '0', '..', '10000', ').)&sr=%7CModifiedDate%7C', '0', '%7C1000'],
            'native_url': ['https://api.encar.com/search/car/list/premium?count=True&q=(And.Hidden.N._.CarType.Y._.(Or.Separation.A._.Separation.B.)_.SellType.%EC%9D%BC%EB%B0%98._.Mileage.range(', '0', '..', '10000', ').)&sr=%7CModifiedDate%7C', '0', '%7C1000']
        }
        self.current_api_url_list = []
        self.session = requests.Session()
        self.headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
                    "Referer": "https://www.encar.com/",
                    "Accept": "application/json, text/plain, */*",
        }
        self.all_ids = set()
        self.new_elems = []

    def run(self):
        self.get_cookies()
        print('Куки получены')
        self.go_through_urls()
        self.session.close()


    def go_through_urls(self):
        '''Функция прохода через все url легковых машин'''
        for api_url_list in self.url_dict.values():
            self.current_api_url_list = api_url_list
            self.get_number_of_results()
            self.go_through_all_mileages()
            self.save_to_db()


    def go_through_all_mileages(self):
        '''Функция прохода через все пробеги легковых машин'''
        for mileage in range(0, 1000000, 10000):
            self.current_api_url_list[1] = str(mileage)
            self.current_api_url_list[3] = str(mileage + 10000)
            print(f'Пробег: от {self.current_api_url_list[1]} до {self.current_api_url_list[3]}')
            self.go_through_all_pages_of_mileage()
        self.current_api_url_list[1] = '0'
        self.current_api_url_list[3] = '10000'


    def go_through_all_pages_of_mileage(self):
        '''Функция прохода через все страницы определенного пробега легковых машин'''
        number_of_results = self.get_number_of_results()
        for page in range(math.ceil(number_of_results/1000)):
            self.current_api_url_list[-2] = str(page*1000)
            response = self.session.get(''.join(self.current_api_url_list), headers=self.headers)    
            data = response.json()['SearchResults']
            print(f'Всего - {response.json()['Count']} Страница {page}. Количество элементов - {len(data)}')
            self.dump_data(data)
        self.current_api_url_list[-2] = '0'


    def dump_data(self, data):
         for elem in data:
            flag_inspection = False
            flag_record = False
            flag_resume = False
            if 'Inspection' in list(elem['Condition']): flag_inspection=True
            if 'Record' in list(elem['Condition']): flag_record=True
            if 'Resume' in list(elem['Condition']): flag_resume=True
            ru_transmission = car_korean_dict['TRANSMISSION'].get(elem.get('Transmission', ''), elem.get('Transmission', ''))
            ru_fuel_type = car_korean_dict['FUEL_TYPE'].get(elem.get('FuelType', ''), elem.get('FuelType', ''))
            ru_cities = car_korean_dict['CITY'].get(elem.get('OfficeCityState', ''), elem.get('OfficeCityState', ''))
            ru_sell_type = car_korean_dict['SELL_TYPE'].get(elem.get('SellType', ''), elem.get('SellType', ''))
            self.new_elems.append(Car(encar_id=elem['Id'],
                                        url=f'https://fem.encar.com/cars/detail/{elem['Id']}',
                                        inspection=flag_inspection,
                                        record=flag_record,
                                        resume=flag_resume,
                                        photo_url=f'https://ci.encar.com/carpicture{elem.get('Photo', '')}',
                                        # manufacturer=elem.get('Manufacturer', ''),
                                        # model=elem.get('Model', ''),
                                        # version=elem.get('Badge', ''),
                                        # version_details=elem.get('BadgeDetail', ''),
                                        transmission=ru_transmission,
                                        fuel_type = ru_fuel_type,
                                        release_date = elem.get('Year', 0),
                                        model_year = elem.get('FormYear', 0),
                                        mileage = elem.get('Mileage', 0),
                                        price = elem.get('Price', 0),
                                        sell_type = ru_sell_type,
                                        updated = elem.get('ModifiedDate', ''),
                                        city = ru_cities
                                        ))

    def get_cookies(self):
        self.session.get("https://www.encar.com", headers=self.headers) 

    def get_number_of_results(self): #он может найти больше 23 тысяч результатов, но в query никогда их не выдаст, потолок - 10000
        return self.session.get(''.join(self.current_api_url_list), headers=self.headers).json()['Count']

    def save_to_db(self):
        Car.objects.bulk_create(self.new_elems, ignore_conflicts=True)
        self.new_elems = []








class TruckParser():
    def __init__(self):
        self.current_mileage = 0
        self.current_page = 0
        self.url_dict = {
            'truck_url': ['https://api.encar.com/search/truck/list/premium?count=True&q=(And.Hidden.N._.(Or.Separation.A._.Separation.B.)_.Mileage.range(', '0', '..', '50000', ').)&sr=%7CModifiedDate%7C', '0', '%7C1000'],
            }
        self.current_api_url_list = []
        self.session = requests.Session()
        self.headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
                    "Referer": "https://www.encar.com/",
                    "Accept": "application/json, text/plain, */*",
        }
        self.all_ids = set()
        self.new_elems = []

    def run(self):
        self.get_cookies()
        print('Куки получены')
        self.go_through_urls()
        self.session.close()


    def go_through_urls(self):
        '''Функция прохода через все url легковых машин'''
        for api_url_list in self.url_dict.values():
            self.current_api_url_list = api_url_list
            self.get_number_of_results()
            self.go_through_all_mileages()
            self.save_to_db()


    def go_through_all_mileages(self):
        '''Функция прохода через все пробеги легковых машин'''
        for mileage in range(0, 2000000, 50000):
            self.current_api_url_list[1] = str(mileage)
            self.current_api_url_list[3] = str(mileage + 50000)
            print(f'Пробег: от {self.current_api_url_list[1]} до {self.current_api_url_list[3]}')
            self.go_through_all_pages_of_mileage()
        self.current_api_url_list[1] = '0'
        self.current_api_url_list[3] = '50000'


    def go_through_all_pages_of_mileage(self):
        '''Функция прохода через все страницы определенного пробега легковых машин'''
        number_of_results = self.get_number_of_results()
        for page in range(math.ceil(number_of_results/1000)):
            self.current_api_url_list[-2] = str(page*1000)
            response = self.session.get(''.join(self.current_api_url_list), headers=self.headers)    
            data = response.json()['SearchResults']
            print(f'Всего - {response.json()['Count']} Страница {page}. Количество элементов - {len(data)}')
            self.dump_data(data)
        self.current_api_url_list[-2] = '0'


    def dump_data(self, data):
         for elem in data:
            flag_inspection = False
            flag_record = False
            flag_resume = False
            if 'Inspection' in list(elem['Condition']): flag_inspection=True
            if 'Record' in list(elem['Condition']): flag_record=True
            if 'Resume' in list(elem['Condition']): flag_resume=True
            eng_manufacturer = truck_korean_dict['MANUFACTURERS'].get(elem.get('Manufacturer', ''), elem.get('Manufacturer', ''))
            ru_fuel_type = truck_korean_dict['FUEL_TYPES'].get(elem.get('FuelType', ''), elem.get('FuelType', ''))
            ru_transmission = truck_korean_dict['TRANSMISSIONS'].get(elem.get('Transmission', ''), elem.get('Transmission', ''))
            eng_model = truck_korean_dict['MODELS'].get(elem.get('Model', ''), elem.get('Model', ''))
            eng_version = truck_korean_dict['VERSIONS'].get(elem.get('Badge', ''), elem.get('Badge', ''))
            ru_cities = truck_korean_dict['CITIES'].get(elem.get('OfficeCityState', ''), elem.get('OfficeCityState', ''))
            ru_version_details = truck_korean_dict['VERSION_DETAILS'].get(elem.get('FormDetail', ''), elem.get('FormDetail', ''))
            ru_usage = truck_korean_dict['USAGES'].get(elem.get('Use', ''), elem.get('Use', ''))
            if '기' in elem.get('Capacity', ''): #прочее/другое
                ru_capacity = ''
            elif '이상' in elem.get('Capacity', ''): # более 톤
                ru_capacity = f'{elem.get('Capacity', '')[:-3]}+ т.'
            else:
                ru_capacity = f'{elem.get('Capacity', '')[:-1]}т.'
            self.new_elems.append(Truck(encar_id=elem['Id'],
                                        url=f'https://fem.encar.com/cars/detail/{elem['Id']}',
                                        category=elem.get('Separation', ''),
                                        trust_service=elem.get('Trust', ''),
                                        inspection=flag_inspection,
                                        record=flag_record,
                                        resume=flag_resume,
                                        photo_url=f'https://ci.encar.com/carpicture{elem.get('Photo', '')}',
                                        manufacturer=eng_manufacturer,
                                        model=eng_model,
                                        version=eng_version,
                                        version_details=ru_version_details,
                                        capacity=ru_capacity,
                                        transmission=ru_transmission,
                                        fuel_type = ru_fuel_type,
                                        release_date = elem.get('Year', 0),
                                        model_year = elem.get('FormYear', 0),
                                        mileage = elem.get('Mileage', 0),
                                        price = elem.get('Price', 0),
                                        usage = ru_usage,
                                        updated = elem.get('ModifiedDate', ''),
                                        city = ru_cities,
                                        )
                                    )

    def get_cookies(self):
        self.session.get("https://www.encar.com", headers=self.headers) 

    def get_number_of_results(self): #он может найти больше 23 тысяч результатов, но в query никогда их не выдаст, потолок - 10000
        return self.session.get(''.join(self.current_api_url_list), headers=self.headers).json()['Count']

    def save_to_db(self):
        Truck.objects.bulk_create(self.new_elems, ignore_conflicts=True)
        self.new_elems = []



        



truck_korean_dict = {
    'MANUFACTURERS' : {
        "이베코": "Iveco",
        "피아트": "Fiat",
        "스카니아": "Scania",
        "타타대우": "Tata Daewoo",
        "조이롱": "Joylong",
        "한국특장": "Hankook Special Vehicle",
        "Yanmar": "Yanmar",
        "대흥중공업": "Daeheung Heavy Industries",
        "이스즈": "Isuzu",
        "만트럭": "MAN Truck",
        "볼보": "Volvo",
        "선롱": "Sunlong",
        "포드": "Ford",
        "기타": "Other",
        "벤츠": "Mercedes-Benz",
        "현대": "Hyundai",
        "폭스바겐": "Volkswagen",
        "닷지": "Dodge",
        "쌍용": "SsangYong",
        "기아(아시아)": "Kia (Asia)",
        "쉐보레": "Chevrolet",
        "캠핑트레일러": "Camping Trailer",
        "대우버스": "Daewoo Bus",
        "르노삼성": "Renault Samsung"
    },
    'MODELS': {
        "유로카고": "Eurocargo",
        "엘프": "Elf",
        "바인스버그": "Weinsberg",
        "포터": "Porter",
        "라이노": "Rhino",
        "노부스 중형트럭": "Novus Medium Truck",
        "구쎈": "Gussen",
        "크나우스": "Knaus",
        "엘디스": "Elddis",
        "대우버스BC": "Daewoo Bus BC",
        "램": "Ram",
        "포레스트 (포터Ⅱ)": "Forest (Porter II)",
        "대우버스BX": "Daewoo Bus BX",
        "슈퍼에어로시티": "Super Aero City",
        "쏘렌토 R": "Sorento R",
        "봉고프론티어": "Bongo Frontier",
        "더쎈": "The CEN",
        "하비": "Hobby",
        "포터 Ⅱ": "Porter II",
        "마스터": "Master",
        "스위프트": "Swift",
        "뉴그랜버드": "New Granbird",
        "에어밴": "Air Van",
        "포레스트 리버": "Forest River",
        "뉴 카운티": "New County",
        "맥쎈": "Maxcen",
        "LESTAR": "Lestar",
        "스프린터": "Sprinter",
        "그랜드 카니발": "Grand Carnival",
        "프리마 덤프": "Prima Dump",
        "더 뉴 봉고Ⅲ": "The New Bongo III",
        "메가트럭": "Mega Truck",
        "코란도 투리스모": "Korando Turismo",
        "e에어로타운": "e-Aero Town",
        "유니버스": "Universe",
        "코스모스": "Cosmos",
        "노부스 대형트럭": "Novus Heavy Truck",
        "기타": "Other",
        "듀오탑": "Duotop",
        "E시리즈": "E-Series",
        "버스형": "Bus Type",
        "마이티 큐티": "Mighty QT",
        "마이티": "Mighty",
        "데일리": "Daily",
        "싼타페 TM": "Santa Fe TM",
        "AM트럭": "AM Truck",
        "글로벌 900 (그린시티)": "Global 900 (Green City)",
        "카고트럭": "Cargo Truck",
        "스타렉스": "Starex",
        "카운티": "County",
        "스타리아": "Staria",
        "렉스턴 스포츠": "Rexton Sports",
        "현대(슈퍼)트럭": "Hyundai (Super) Truck",
        "프리마 중형트럭": "Prima Medium Truck",
        "렉스턴 스포츠 칸": "Rexton Sports Khan",
        "카니발 R": "Carnival R",
        "복사와이드": "Besta Wide",
        "두카토": "Ducato",
        "비스너": "Büsner",
        "프리마": "Prima",
        "무한괘도식": "Crawler Type",
        "파맥스": "Pamax",
        "노부스 덤프": "Novus Dump",
        "e마이티": "e-Mighty",
        "대형트럭(91A)": "Heavy Truck (91A)",
        "더 뉴 레이": "The New Ray",
        "아드리아": "Adria",
        "올 뉴 마이티": "All New Mighty",
        "더 뉴 카렌스": "The New Carens",
        "대우버스BH": "Daewoo Bus BH",
        "마이티2": "Mighty 2",
        "두에고": "DuEgo",
        "차세대트럭": "Next-Generation Truck",
        "코란도 스포츠": "Korando Sports",
        "더 뉴 카니발": "The New Carnival",
        "네오오토": "NeoAuto",
        "대우버스BS": "Daewoo Bus BS",
        "뉴포터": "New Porter",
        "에어로타운": "Aero Town",
        "뉴파워트럭": "New Power Truck",
        "유니시티": "UniCity",
        "엑시언트": "Xcient",
        "봉고Ⅲ": "Bongo III",
        "e카운티": "e-County",
        "프리마 대형트럭": "Prima Heavy Truck",
        "티볼리 에어": "Tivoli Air",
        "더 뉴 그랜드 스타렉스": "The New Grand Starex",
        "트라고": "Trago",
        "그랜드 스타렉스": "Grand Starex",
        "팰리세이드": "Palisade",
        "덤프": "Dump",
        "세레스": "Ceres",
        "트렌짓": "Transit",
        "대우버스FX": "Daewoo Bus FX",
        "트렉터": "Tractor",
        "리베로": "Libero",
        "카니발 4세대": "Carnival 4th Gen",
        "그랜드 캘리포니아": "Grand California",
        "중형트럭(91A)": "Medium Truck (91A)",
        "E6": "E6",
        "대형트럭": "Heavy Truck",
        "G4 렉스턴": "G4 Rexton",
        "코나": "Kona",
        "쏠라티": "Solati",
        "파비스": "Pavise",
        "익스프레스밴": "Express Van"
    },
    'VERSIONS': {
        "090 25인승": "090 25-seater",
        "럭셔리": "Luxury",
        "롱바디 GOLD 25인승": "Long Body GOLD 25-seater",
        "장축 리무진 11인승": "Long Wheelbase Limousine 11-seater",
        "GOLD": "GOLD",
        "장축 GOLD 29인승": "Long Wheelbase GOLD 29-seater",
        "엘레강스": "Elegance",
        "120 46인승": "120 46-seater",
        "프레미오": "Premio",
        "D500": "D500",
        "표준형 SUP 20인승": "Standard SUP 20-seater",
        "일반캡 LPG": "Standard Cab LPG",
        "106 47인승": "106 47-seater",
        "디젤 42인승": "Diesel 42-seater",
        "일반캡": "Standard Cab",
        "내로우캡": "Narrow Cab",
        "쥐트빈트": "Zitwind",
        "디젤": "Diesel",
        "슈퍼캡 LPG": "Super Cab LPG",
        "스탠다드": "Standard",
        "4WD": "4WD",
        "SUP": "SUP",
        "롱바디 35인승": "Long Body 35-seater",
        "장축 DLX 12인승": "Long Wheelbase DLX 12-seater",
        "더블캡 CRDI": "Double Cab CRDI",
        "4WD 킹캡": "4WD King Cab",
        "롱바디 DLX 39인승": "Long Body DLX 39-seater",
        "터보인터쿨러 일반캡": "Turbo Intercooler Standard Cab",
        "VIO17": "VIO17",
        "디젤 38인승": "Diesel 38-seater",
        "락우드": "Rockwood",
        "장축 리무진 15인승": "Long Wheelbase Limousine 15-seater",
        "초장축 어린이 33인승": "Extra Long Wheelbase Kids 33-seater",
        "8X2": "8X2",
        "롱바디 SUP 29인승": "Long Body SUP 29-seater",
        "롱바디 30인승": "Long Body 30-seater",
        "6X4 저상": "6X4 Low Floor",
        "디젤 46인승": "Diesel 46-seater",
        "장축 어린이 39인승": "Long Wheelbase Kids 39-seater",
        "와이드캡 GOLD": "Wide Cab GOLD",
        "35인승": "35-seater",
        "장축 GOLD 16인승": "Long Wheelbase GOLD 16-seater",
        "바이엘 스마트": "Bayer Smart",
        "슬리퍼캡": "Sleeper Cab",
        "39인승": "39-seater",
        "12인승": "12-seater",
        "표준형 DLX 25인승": "Standard DLX 25-seater",
        "슈퍼캡 TCI": "Super Cab TCI",
        "LPI": "LPI",
        "슈퍼캡 CRDI": "Super Cab CRDI",
        "4WD 더블캡": "4WD Double Cab",
        "표준캡": "Standard Cab",
        "킹캡 TCI": "King Cab TCI",
        "8X4": "8X4",
        "롱바디 23인승": "Long Body 23-seater",
        "4WD 킹캡 LPG": "4WD King Cab LPG",
        "장축 스페셜 25인승": "Long Wheelbase Special 25-seater",
        "장축 GOLD 20인승": "Long Wheelbase GOLD 20-seater",
        "4X4": "4X4",
        "10x4": "10X4",
        "컴포트": "Comfort",
        "090 34인승": "090 34-seater",
        "115 46인승": "115 46-seater",
        "터보인터쿨러 슈퍼캡": "Turbo Intercooler Super Cab",
        "아도라": "Adora",
        "아버소": "Averso",
        "6X4 후삼축": "6X4 Rear Triple Axle",
        "더블캡 LPG": "Double Cab LPG",
        "4WD 표준캡": "4WD Standard Cab",
        "4WD 슈퍼캡 LPG": "4WD Super Cab LPG",
        "단축 STD 25인승": "Short Wheelbase STD 25-seater",
        "롱바디 34인승": "Long Body 34-seater",
        "롱바디 SUP 25인승": "Long Body SUP 25-seater",
        "기타": "Other",
        "20인승": "20-seater",
        "일반캡 CRDI": "Standard Cab CRDI",
        "노블": "Noble",
        "47인승": "47-seater",
        "29인승": "29-seater",
        "장축 어린이 21인승": "Long Wheelbase Kids 21-seater",
        "롱바디 리무진 15인승": "Long Body Limousine 15-seater",
        "슈퍼캡 디젤": "Super Cab Diesel",
        "34인승": "34-seater",
        "표준형 SUP 25인승": "Standard SUP 25-seater",
        "킹캡": "King Cab",
        "데이캡": "Day Cab",
        "212S 42인승": "212S 42-seater",
        "표준캡 LPG": "Standard Cab LPG",
        "8x4": "8X4",
        "표준캡 CRDI": "Standard Cab CRDI",
        "프라임": "Prime",
        "디젤 59인승": "Diesel 59-seater",
        "4WD 더블캡 LPG": "4WD Double Cab LPG",
        "4WD 표준캡 LPG": "4WD Standard Cab LPG",
        "6X2": "6X2",
        "단축 어린이 34인승": "Short Wheelbase Kids 34-seater",
        "카라원 390": "CaraOne 390",
        "장축 투어 15인승": "Long Wheelbase Tour 15-seater",
        "090 35인승": "090 35-seater",
        "212S 45인승": "212S 45-seater",
        "CNG 58인승": "CNG 58-seater",
        "090 67인승": "090 67-seater",
        "장축 SUP 20인승": "Long Wheelbase SUP 20-seater",
        "더블캡 TCI": "Double Cab TCI",
        "장축 SUP 25인승": "Long Wheelbase SUP 25-seater",
        "8X4 후삼축": "8X4 Rear Triple Axle",
        "로얄": "Royal",
        "롱바디 21인승": "Long Body 21-seater",
        "디럭스": "Deluxe",
        "등급 없음": "No Grade",
        "7인승": "7-seater",
        "일렉트릭 33인승": "Electric 33-seater",
        "표준형 SUP 15인승": "Standard SUP 15-seater",
        "090 30인승": "090 30-seater",
        "표준형 STD 25인승": "Standard STD 25-seater",
        "4X2 표준": "4X2 Standard",
        "킹캡 EV": "King Cab EV",
        "42인승": "42-seater",
        "일반캡 TCI": "Standard Cab TCI",
        "6X4": "6X4",
        "18인승": "18-seater",
        "수퍼디럭스": "Super Deluxe",
        "슈퍼캡": "Super Cab",
        "단축 SUP 25인승": "Short Wheelbase SUP 25-seater",
        "롱바디 38인승": "Long Body 38-seater",
        "4WD 일반캡 LPG": "4WD Standard Cab LPG",
        "프리미엄": "Premium",
        "단축 어린이 20인승": "Short Wheelbase Kids 20-seater",
        "슈퍼캡 일렉트릭(EV)": "Super Cab Electric (EV)",
        "표준캡 TCI": "Standard Cab TCI",
        "프레스티지": "Prestige",
        "표준형 30인승": "Standard 30-seater",
        "장축 SUP 29인승": "Long Wheelbase SUP 29-seater",
        "와이드캡 프리미엄": "Wide Cab Premium",
        "표준형 DLX 34인승": "Standard DLX 34-seater",
        "116 46인승": "116 46-seater",
        "롱바디 SUP 24인승": "Long Body SUP 24-seater",
        "10X4": "10X4",
        "표준형 34인승": "Standard 34-seater",
        "어피니티": "Affinity",
        "카라원 480": "CaraOne 480",
        "캠핑카": "Camping Car",
        "8X4": "8X4",
        "25인승": "25-seater",
        "장축 GOLD 25인승": "Long Wheelbase GOLD 25-seater",
        "4WD 일반캡": "4WD Standard Cab",
        "울트라": "Ultra",
        "600": "600",
        "펜타 슬리퍼캡": "Penta Sleeper Cab",
        "장축 어린이 29인승": "Long Wheelbase Kids 29-seater",
        "212H 29인승": "212H 29-seater",
        "스프라이트": "Sprite",
        "GOLD 25인승": "GOLD 25-seater",
        "212 22인승 리무진": "212 22-seater Limousine",
        "더블캡 디젤": "Double Cab Diesel",
        "4x4 일반캡": "4X4 Standard Cab",
        "4WD 슈퍼캡": "4WD Super Cab",
        "SUP 25인승": "SUP 25-seater",
        "4X2": "4X2",
        "더블캡": "Double Cab",
        "19인승": "19-seater",
        "AVT2042He": "AVT2042He",
        "킹캡 CRDI": "King Cab CRDI",
        "일반캡 4WD": "Standard Cab 4WD",
        "CRDI 슈퍼캡": "CRDI Super Cab",
        "단축 DLX 25인승": "Short Wheelbase DLX 25-seater",
        "킹캡 LPG": "King Cab LPG",
        "2WD": "2WD"
    },
    'FUEL_TYPES': {
        "전기": "Электричество",
        "가솔린": "Бензин",
        "LPG(일반인 구입)": "Пропан-бутан (Газ)",
        "디젤": "Дизель",
        "CNG": "Метан (Газ)",
        "기타": "Другое"
    },
    'TRANSMISSIONS': {
        "수동": "Механическая",
        "오토": "Автоматическая",
        "세미오토": "Полуавтоматическая",
        "기타": "Другое"
    },
    'CITIES': {
        "충남": "Чхуннам (пров. Чхунчхон-Намдо)",
        "울산": "Ульсан",
        "광주": "Кванджу",
        "경남": "Кённам (пров. Кёнсан-Намдо)",
        "경기": "Кёнги (пров. Кёнгидо)",
        "강원": "Канвон (пров. Канвондо)",
        "충북": "Чхунбук (пров. Чхунчхон-Пукто)",
        "부산": "Пусан",
        "대구": "Тэгу",
        "경북": "Кёнбук (пров. Кёнсан-Пукто)",
        "전남": "Чолланам (пров. Чолла-Намдо)",
        "인천": "Инчхон",
        "세종": "Седжон",
        "전북": "Чолла-Пукто (Чоллабук)",
        "제주": "Чеджу",
        "서울": "Сеул",
        "대전": "Тэджон",
    },

    'USAGES': {
        "등본차량": "Служебный автомобиль",
        "영업용": "Коммерческий транспорт",
        "자가용": "Личный автомобиль",
    },

    'VERSION_DETAILS' : {
        "음식물수거": "Мусоровоз для пищевых отходов",
        "특수/케미컬(VOC,테플론)탱크로리": "Спецтехника / химический (VOC, тефлон) танкер",
        "오가크레인": "Автокран (O.G.A. кран)",
        "워킹플로어": "Кузов с подвижным полом (Walking Floor)",
        "집게차": "Манипулятор с грейфером",
        "준설차": "Дноочистительная машина / земснаряд",
        "익스(하이)내장탑": "Фургон изотермический (High-EX)",
        "익스(하이)냉장탑": "Рефрижератор (High-EX)",
        "언더리프트": "Эвакуатор с подкатом (Underlift)",
        "저상형 윙바디": "Низкорамный фургон с боковым открытием (Wing body)",
        "사료운반차": "Кормовоз",
        "컨테이너 샤시": "Шасси-контейнеровоз",
        "암롤/롤온": "Мультилифт (Amroll / Roll-on)",
        "냉동탑": "Фургон-рефрижератор (морозильный)",
        "활어차": "Автоцистерна для живой рыбы",
        "살수차": "Поливомоечная машина",
        "이동/광고/응급차": "Передвижная реклама / спецмашина / скорая",
        "익스(하이)내장탑 파워게이트": "Фургон изотермический High-EX с гидробортом",
        "냉동윙": "Фургон-рефрижератор с боковым открытием (Reefer Wing)",
        "이동식 목욕차": "Передвижная баня / душ",
        "냉장윙": "Рефрижераторный фургон (охлаждаемый) с боковым открытием",
        "캠핑트레일러": "Кемпинг-трейлер",
        "카고(화물)트럭": "Грузовой бортовой автомобиль",
        "압착진개": "Мусоровоз-компактор (с прессом)",
        "트렉터": "Тягач (трактор-седельный)",
        "바가지차": "Автокран с ковшом (автовышка-«ковшевик»)",
        "냉동탑 파워게이트": "Фургон-рефрижератор с гидробортом",
        "내장탑 파워게이트": "Изотермический фургон с гидробортом",
        "기타": "Прочее",
        "진개덤프": "Самосвал-мусоровоз",
        "저상형 내장탑": "Низкорамный изотермический фургон",
        "윙바디 파워게이트": "Фургон с боковым открытием (Wing body) и гидробортом",
        "사다리차": "Автолестница",
        "재활용품수집차": "Мусоровоз для раздельного сбора",
        "굴삭기": "Экскаватор",
        "익스(하이)냉동탑 파워게이트": "High-EX рефрижератор с гидробортом",
        "유류/액상탱크로리": "Автоцистерна для ГСМ/жидкостей",
        "저상형 냉장탑": "Низкорамный рефрижератор",
        "캠핑카": "Кемпер (дом на колесах)",
        "저상형 냉동탑": "Низкорамный фургон-рефрижератор (морозильный)",
        "셀프로더": "Самопогрузчик",
        "압축진개": "Мусоровоз-пресс (компрессионный)",
        "노면청소차": "Подметально-уборочная машина",
        "윙바디": "Фургон с боковым открытием (Wing body)",
        "익스(하이)냉동탑": "High-EX фургон-рефрижератор",
        "보냉윙": "Изотермический фургон с боковым открытием",
        "익스(하이)냉장탑 파워게이트": "High-EX рефрижераторный фургон с гидробортом",
        "내장탑": "Изотермический фургон",
        "씨티/워크스루밴": "Сити-вэн / фургон Walk-through",
        "냉온장탑": "Фургон с климат-контролем (тепло-холод)",
        "버스": "Автобус",
        "상승내장탑": "Фургон с подъемным кузовом (Lift-up)",
        "버큠로리": "Вакуумная машина (ассенизатор)",
        "로우베드/릴리리": "Низкорамный трейлер (Low-bed trailer)",
        "활선차(고소작업)": "Автовышка для работы под напряжением",
        "저상형 내장탑 파워게이트": "Низкорамный изотермический фургон с гидробортом",
        "톱밥운반차": "Опилкивоз",
        "다용도탑": "Многофункциональный фургон",
        "냉장탑": "Фургон-рефрижератор (охлаждаемый)",
        "트랜스/와이드 파워게이트": "Широкий фургон с гидробортом (Wide PG)",
        "카케리어": "Автовоз",
        "윙트레일러": "Трейлер с боковым открытием (Wing trailer)",
        "카고크레인": "Бортовой грузовик с краном-манипулятором",
        "파워게이트": "Гидроборт (Power gate)",
        "덤프": "Самосвал",
    }
}



car_korean_dict = {
    'MANUFACTURER': {
        "도요타": "Toyota",
        "BMW": "BMW",
        "어큐라": "Acura",
        "알파 로메오": "Alfa Romeo",
        "스즈키": "Suzuki",
        "이네오스": "Ineos",
        "로터스": "Lotus",
        "아우디": "Audi",
        "기타 제조사": "Other Manufacturers",
        "뷰익": "Buick",
        "마세라티": "Maserati",
        "KG모빌리티(쌍용)": "KG Mobility (SsangYong)",
        "쉐보레(GM대우)": "Chevrolet (GM Daewoo)",
        "르노코리아(삼성)": "Renault Korea (Samsung)",
        "머큐리": "Mercury",
        "기타 수입차": "Other Imports",
        "폴스타": "Polestar",
        "북기은상": "BAIC Yinxiang",
        "벤틀리": "Bentley",
        "크라이슬러": "Chrysler",
        "마쯔다": "Mazda",
        "미쯔비시": "Mitsubishi",
        "링컨": "Lincoln",
        "테슬라": "Tesla",
        "쉐보레": "Chevrolet",
        "사브": "Saab",
        "BYD": "BYD",
        "시트로엥/DS": "Citroën / DS",
        "동풍소콘": "DFSK (Dongfeng Sokon)",
        "험머": "Hummer",
        "마이바흐": "Maybach",
        "사이언": "Scion",
        "재규어": "Jaguar",
        "기아": "Kia",
        "랜드로버": "Land Rover",
        "스바루": "Subaru",
        "렉서스": "Lexus",
        "캐딜락": "Cadillac",
        "지프": "Jeep",
        "포드": "Ford",
        "GMC": "GMC",
        "혼다": "Honda",
        "벤츠": "Mercedes-Benz",
        "미쯔오까": "Mitsuoka",
        "스마트": "Smart",
        "롤스로이스": "Rolls-Royce",
        "미니": "MINI",
        "제네시스": "Genesis",
        "인피니티": "Infiniti",
        "페라리": "Ferrari",
        "피아트": "Fiat",
        "애스턴마틴": "Aston Martin",
        "닷지": "Dodge",
        "다이하쯔": "Daihatsu",
        "볼보": "Volvo",
        "닛산": "Nissan",
        "람보르기니": "Lamborghini",
        "맥라렌": "McLaren",
        "포르쉐": "Porsche",
        "현대": "Hyundai",
        "폭스바겐": "Volkswagen",
        "푸조": "Peugeot",
        "링야오": "Lynk & Co",
        "쌍용": "SsangYong",
        "재규어랜드로버": "Jaguar Land Rover",
        "GAC": "GAC",
    },
    'TRANSMISSION': {
        "수동": "Механическая",
        "오토": "Автоматическая",
        "기타": "Прочее",
        "세미오토": "Роботизированная",
        "CVT": "Вариатор (CVT)"
    },
    'SELL_TYPE': {
        "렌트": "Аренда",
        "리스": "Лизинг",
        "일반": "Обычная покупка"
    },
    'CITY': {
        "충남": "Чхунчхон-Намдо",
        "서울": "Сеул",
        "세종": "Седжон",
        "부산": "Пусан",
        "강원": "Канвондо",
        "광주": "Кванджу",
        "경북": "Кёнсан-Пукто",
        "충북": "Чхунчхон-Пукто",
        "전남": "Чолла-Намдо",
        "대구": "Тэгу",
        "제주": "Чеджу",
        "전북": "Чолла-Пукто",
        "경남": "Кёнсан-Намдо",
        "인천": "Инчхон",
        "울산": "Ульсан",
        "경기": "Кёнгидо",
        "대전": "Тэджон"
    },
    'FUEL_TYPE': {
        "LPG+전기": "Газ (пропан-бутан) + Электро",
        "가솔린": "Бензин",
        "가솔린+전기": "Бензин + Электро",
        "기타": "Прочее",
        "수소": "Водород",
        "가솔린+CNG": "Бензин + Метан",
        "디젤": "Дизель",
        "전기": "Электро",
        "가솔린+LPG": "Бензин + Газ (пропан-бутан)",
        "디젤+전기": "Дизель + Электро",
        "LPG(일반인 구입)": "Газ (пропан-бутан)"
    },
    'COLOR': {
        "주황색": "Оранжевый",
        "녹색": "Зелёный",
        "연두색": "Салатовый",
        "은색투톤": "Серебристый (двухцветный)",
        "갈대색": "Бежевый",
        "검정투톤": "Чёрный (двухцветный)",
        "갈색": "Коричневый",
        "담녹색": "Тёмно-зелёный",
        "흰색": "Белый",
        "금색투톤": "Золотистый (двухцветный)",
        "연금색": "Светло-золотистый (Шампань)",
        "청색": "Синий",
        "금색": "Золотистый",
        "은색": "Серебристый",
        "명은색": "Светло-серебристый",
        "분홍색": "Розовый",
        "검정색": "Чёрный",
        "하늘색": "Голубой",
        "쥐색": "Серый",
        "은하색": "Серебристо-серый (Металлик)",
        "은회색": "Серо-серебристый",
        "흰색투톤": "Белый (двухцветный)",
        "빨간색": "Красный",
        "자주색": "Бордовый",
        "노란색": "Жёлтый",
        "진주색": "Перламутровый",
        "보라색": "Фиолетовый",
        "청옥색": "Бирюзовый",
        "갈색투톤": "Коричневый (двухцветный)"
    }
}



OPTIONS = {
    'CAR': {
        "001": "Антиблокировочная система (ABS)",
        "002": "Электронно-регулируемая подвеска (ECS)",
        "003": "CD-проигрыватель",
        "004": "Передний мультимедиа-экран",
        "005": "Навигационная система",
        "006": "Электропривод замков дверей",
        "007": "Электростеклоподъёмники",
        "008": "Гидроусилитель руля",
        "010": "Люк",
        "014": "Кожаный салон",
        "015": "Центральный замок с ДУ",
        "017": "Легкосплавные диски",
        "019": "Система курсовой устойчивости (TCS)",
        "020": "Боковые подушки безопасности",
        "021": "Электропривод передних сидений",
        "022": "Подогрев передних и задних сидений",
        "023": "Климат-контроль",
        "024": "Складывающиеся боковые зеркала с электроприводом",
        "026": "Фронтальные подушки безопасности",
        "027": "Фронтальные подушки безопасности",
        "029": "Фары (ксенон/LED)",
        "030": "Электрохромное зеркало заднего вида",
        "031": "Мультируль",
        "032": "Датчики парковки (перед/зад)",
        "033": "Система контроля давления в шинах (TPMS)",
        "034": "Вентилируемые передние сиденья",
        "035": "Электропривод передних сидений",
        "051": "Сиденья с памятью настроек",
        "054": "Задний мультимедиа-экран",
        "055": "Электронная система стабилизации (ESC)",
        "056": "Шторки безопасности (Air Curtain)",
        "057": "Смарт-ключ",
        "058": "Камера заднего вида",
        "059": "Электропривод багажника",
        "062": "Рейлинги на крыше",
        "063": "Подогрев передних и задних сидений",
        "068": "Круиз-контроль (обычный/адаптивный)",
        "071": "AUX-вход",
        "072": "USB-порт",
        "074": "Hi-pass (автооплата дорог)",
        "075": "Фары (ксенон/LED)",
        "077": "Вентилируемые передние сиденья",
        "078": "Сиденья с памятью настроек",
        "079": "Круиз-контроль (обычный/адаптивный)",
        "080": "Электропривод дверей",
        "081": "Датчик дождя",
        "082": "Подогрев рулевого колеса",
        "083": "Электрорегулировка рулевой колонки",
        "084": "Подрулевые лепестки переключения передач",
        "085": "Датчики парковки (перед/зад)",
        "086": "Система контроля слепых зон (BSW)",
        "087": "Камеры кругового обзора (360°)",
        "088": "Система удержания в полосе (LDWS)",
        "089": "Электропривод задних сидений",
        "090": "Вентилируемые задние сиденья",
        "091": "Массажные сиденья",
        "092": "Солнцезащитные шторки для задних сидений",
        "093": "Солнцезащитные шторки для задних сидений",
        "094": "Электронный стояночный тормоз (EPB)",
        "095": "Проекционный дисплей (HUD)",
        "096": "Bluetooth",
        "097": "Автоматический свет",
    },

    'TRUCK': {
        "001": "Гидроборт (Power Gate)",
        "002": "Легкосплавные диски",
        "003": "Люк",
        "004": "Складывающиеся боковые зеркала с электроприводом",
        "005": "Электропривод откидной кабины",
        "006": "Спойлер на крыше",
        "007": "ВОМ (вал отбора мощности)",
        "008": "Электрический сигнал (клаксон)",
        "009": "Газовый компрессор",  # в API какой-то греческий???
        "010": "Система снижения дымности",
        "011": "Мультируль",
        "012": "Гидроусилитель руля",
        "013": "Вентилируемые передние сиденья",
        "014": "Кожаный салон",
        "015": "Подогрев передних сидений",
        "016": "Подогреваемая спальная полка",
        "017": "ECM (электронный блок управления двигателем)",
        "018": "Ретардер (гидравлический тормоз-замедлитель)",
        "019": "Антиблокировочная система (ABS)",
        "020": "ASR/TCS (система против пробуксовки)",
        "021": "Пневматические тормоза",
        "022": "Система контроля давления в шинах (TPMS)",
        "023": "EHS (помощь при старте на подъеме)",
        "024": "Тахометр",
        "025": "Подушка безопасности (водительская)",
        "026": "Камера заднего вида",
        "027": "Кондиционер (ручной)",
        "028": "Климат-контроль",
        "029": "Отопитель/кондиционер Mushidong",  # брендовый, оставил оригинал
        "030": "Центральный замок с ДУ",
        "031": "Электростеклоподъёмники",
        "032": "Круиз-контроль",
        "033": "CD-проигрыватель",
        "034": "Навигационная система",
        "035": "AUX-вход",
        "036": "USB-порт",
        "037": "Холодильник",
    }
}