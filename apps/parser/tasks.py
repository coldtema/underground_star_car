from celery import shared_task, chain
from apps.parser.parsers import async_clearer, async_parser, diag_parser, raw_parser, record_parser
from parser import ru_price_calc


@shared_task
def get_raw_car_info():
    '''Собираем инфу из полного каталога машин (батч по пробегам)'''
    p = raw_parser.CarParser()
    p.run()
    del p
    return True


@shared_task
def get_raw_truck_info():
    '''Собираем инфу из полного каталога траков (батч по пробегам)'''
    p = raw_parser.TruckParser()
    p.run()
    del p
    return True


@shared_task
def get_full_car_info():
    '''Собираем полую инфу отдельно из каждого url машины'''
    p = async_parser.AsyncCarParser()
    p.run()
    del p
    return True


@shared_task
def get_full_truck_info():
    '''Собираем полую инфу отдельно из каждого url трака'''
    p = async_parser.AsyncTruckParser()
    p.run()
    del p
    return True


def delete_fake_cars():
    '''Удаляем машины не для продажи в рф + дубли'''
    p = async_parser.DuplicateClearer()
    p.go_through_unique_dummy_ids()
    del p
    return True


@shared_task
def get_car_diagnosis():
    '''Собираем инфу о состоянии кузова всех машин'''
    p = diag_parser.AsyncCarDiagParser()
    p.run()
    del p
    return True


@shared_task
def get_car_record():
    '''Собираем инфу о страховых случаях каждой машины'''
    p = record_parser.AsyncCarRecordParser()
    p.run()
    del p
    return True


@shared_task
def count_duties_and_ru_price():
    '''Расчет таможенных сборов и ру-цены для каждой машины'''
    p = ru_price_calc.RuPriceCalc()
    p.run()
    del p
    return True


@shared_task
def delete_not_avaliable():
    '''Удаление неактуальных объявлений'''
    p = async_clearer.AsyncCarClearer()
    p.run()
    del p
    return True


@shared_task
def main_task_car():
    '''Полностью добавляет новые машины со всей подробной инфой в бд (раз в 3 часа)'''
    chain(
        get_raw_car_info.si(),
        get_full_car_info.si(),
        delete_fake_cars.si(),
        get_car_diagnosis.si(),
        get_car_record.si(),
        count_duties_and_ru_price.si(),
    )()
    return True


@shared_task
def easy_task_car():
    '''Удаляет неактуальные объявления + пересчитывает таможенные сборы и ру цену (раз в час)'''
    chain(
        delete_not_avaliable.si(),
        count_duties_and_ru_price.si(),
    )()
    return True