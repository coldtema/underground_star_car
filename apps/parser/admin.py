from django.contrib import admin
from .models import TruckOption, OptionCategory, CarOption


@admin.register(TruckOption)
class TruckOptionAdmin(admin.ModelAdmin):
    list_display = ['encar_id', 'name', 'category']


@admin.register(CarOption)
class CarOptionAdmin(admin.ModelAdmin):
    list_display = ['encar_id', 'name', 'category']


@admin.register(OptionCategory)
class OptionCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']