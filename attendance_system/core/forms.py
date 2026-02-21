from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from datetime import date

from .models import Subject, ClassYear

class SimpleRegisterForm(UserCreationForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }


class QRGenerateForm(forms.Form):
    class_year = forms.ModelChoiceField(queryset=ClassYear.objects.all())
    subject = forms.ModelChoiceField(queryset=Subject.objects.all())
    date = forms.DateField(initial=date.today, widget=forms.DateInput(attrs={'type': 'date'}))
