from django.db import models


class FuelType(models.TextChoices):
    GASOLINE = "G", "Бензин"
    DIESEL = "D", "Дизель"
    LPG = "L", "Газ"
    GASOLINE_ELECTRIC = "GE", "Бензин + Электро"
    DIESEL_ELECTRIC = "DE", "Дизель + Электро"
    LPG_ELECTRIC = "LE", "Газ + Электро"
    LPG_GASOLINE = "LG", "Газ + Бензин"
    ELECTRIC = "E", "Электро"
    HYDROGEN = "HY", "Водород"


class Condition(models.TextChoices):
    NORMAL = 'NORMAL', 'НОРМ.'
    REPLACEMENT = 'REPLACEMENT', 'ЗАМЕНА'


class AccidentType(models.TextChoices):
    TYPE1 = '1', 'Урегулировано страховой владельца данного авто'
    TYPE2 = '2', 'Возмещение за счет страховой виновника'
    TYPE3 = '3', 'С ущербом чужому здоровью или имуществу'



class Car(models.Model):
    encar_id = models.BigIntegerField(verbose_name='Внутреннее id encar', unique=True)
    url = models.URLField()
    inspection = models.BooleanField(default=False)
    record = models.BooleanField(default=False)
    resume = models.BooleanField(default=False)
    photo_url = models.CharField(max_length=256)
    photos_codes = models.CharField(max_length=512, null=True, blank=True)
    manufacturer = models.CharField(max_length=128, null=True, blank=True)
    model = models.CharField(max_length=128, null=True, blank=True)
    version = models.CharField(max_length=128, null=True, blank=True)
    version_details = models.CharField(max_length=128, null=True, blank=True)
    color = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    engine_capacity = models.IntegerField(null=True, blank=True, db_index=True)
    transmission = models.CharField(max_length=128, db_index=True)
    fuel_type = models.CharField(max_length=2, choices=FuelType.choices, default=FuelType.GASOLINE, db_index=True)
    release_date = models.IntegerField(db_index=True)
    model_year = models.IntegerField()
    mileage = models.IntegerField(db_index=True)
    options = models.CharField(max_length=1024, null=True, blank=True)
    price = models.BigIntegerField()
    ru_price = models.IntegerField(null=True, blank=True)
    customs_duty = models.IntegerField(null=True, blank=True)
    recycling_fee = models.IntegerField(null=True, blank=True)
    sell_type = models.CharField(max_length=128)
    updated = models.DateTimeField()
    city = models.CharField(max_length=128)
    korean_number = models.CharField(max_length=32, null=True, blank=True)
    dummy_id = models.IntegerField(null=True, blank=True, db_index=True)
    encar_diag = models.IntegerField(null=True, blank=True) # -1 - нет, 1 - да


class Diagnosis(models.Model):
    left_front_door = models.CharField(max_length=16, choices=Condition.choices)
    left_back_door = models.CharField(max_length=16, choices=Condition.choices)
    right_front_door = models.CharField(max_length=16, choices=Condition.choices)
    right_back_door = models.CharField(max_length=16, choices=Condition.choices)
    trunk = models.CharField(max_length=16, choices=Condition.choices)
    hood = models.CharField(max_length=16, choices=Condition.choices)
    front_fender_right = models.CharField(max_length=16, choices=Condition.choices)
    front_fender_left = models.CharField(max_length=16, choices=Condition.choices)
    car = models.OneToOneField(Car, on_delete=models.CASCADE, null=True, blank=True, related_name='diagnosis')


class Truck(models.Model):
    encar_id = models.BigIntegerField(verbose_name='Внутреннее id encar', unique=True)
    url = models.URLField()
    category = models.CharField(max_length=1)
    trust_service = models.CharField(max_length=50)
    inspection = models.BooleanField(default=False)
    record = models.BooleanField(default=False)
    resume = models.BooleanField(default=False)
    photo_url = models.CharField(max_length=256)
    photos_codes = models.CharField(max_length=512, null=True, blank=True)
    manufacturer = models.CharField(max_length=128, null=True, blank=True)
    model = models.CharField(max_length=128, null=True, blank=True)
    version = models.CharField(max_length=128, null=True, blank=True)
    version_details = models.CharField(max_length=128, null=True, blank=True)
    color = models.CharField(max_length=128, null=True, blank=True)
    engine_capacity = models.IntegerField(null=True, blank=True)
    horse_power = models.IntegerField(null=True, blank=True)
    capacity = models.CharField(max_length=32)
    transmission = models.CharField(max_length=128)
    fuel_type = models.CharField(max_length=2, choices=FuelType.choices, default=FuelType.GASOLINE)
    release_date = models.IntegerField()
    model_year = models.IntegerField()
    mileage = models.IntegerField()
    options = models.CharField(max_length=1024, null=True, blank=True)
    price = models.BigIntegerField()
    usage = models.CharField(max_length=128)
    updated = models.DateTimeField()
    city = models.CharField(max_length=128)
    korean_number = models.CharField(max_length=32, null=True, blank=True)

class Vechile(models.TextChoices):
    CAR = 'CAR', 'CAR'
    TRUCK = 'TRUCK', 'TRUCK'

class OptionCategory(models.Model):
    name = models.CharField(max_length=64)
    vechile = models.CharField(max_length=5, choices=Vechile.choices, default=Vechile.TRUCK)

    def __str__(self):
        return self.name

class TruckOption(models.Model):
    encar_id = models.CharField(max_length=3)
    name = models.CharField(max_length=128)
    category = models.ForeignKey(OptionCategory, on_delete=models.CASCADE)


class CarOption(models.Model):
    encar_id = models.CharField(max_length=3)
    name = models.CharField(max_length=128)
    category = models.ForeignKey(OptionCategory, on_delete=models.CASCADE)


class CarRecord(models.Model):
    owner_count = models.IntegerField()
    other_accident_cost = models.IntegerField(default=0)
    other_accident_count = models.IntegerField(default=0)
    driver_accident_cost = models.IntegerField(default=0)
    driver_accident_count = models.IntegerField(default=0)
    car = models.OneToOneField(Car, on_delete=models.CASCADE, related_name='car_record')


class Accident(models.Model):
    type_of_accident = models.CharField(max_length=1, choices=AccidentType.choices)
    date = models.DateField()
    insurance_benefit = models.IntegerField(default=0)
    part_cost = models.IntegerField(default=0)
    labor_cost = models.IntegerField(default=0)
    painting_cost = models.IntegerField(default=0)
    car_record = models.ForeignKey(CarRecord, on_delete=models.CASCADE)