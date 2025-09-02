from django import forms

class CarArtikulForm(forms.Form):
    artikul = forms.CharField(
        label='Артикул',
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Например: 38877922', 'class': 'input'}))
    
    KIND_CHOICES = (
        ('car', 'Легковой (car)'),
        ('truck', 'Грузовой (truck)'))


    kind = forms.ChoiceField(
        label='Тип ТС',
        choices=KIND_CHOICES,
        widget=forms.RadioSelect)