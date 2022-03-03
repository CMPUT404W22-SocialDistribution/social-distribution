from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

from .models import Author

class SignUpForm(UserCreationForm):
    username = forms.CharField()
    displayName = forms.CharField(max_length=200, required=False)
    github = forms.CharField(required=False, help_text='Optional')    

    class Meta: 
        model = User
        fields = ('username', 'displayName', 'github', 'password1', 'password2')
    
    def clean(self):
        cleaned_data = self.cleaned_data
        username = cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Username already exists.')

        if cleaned_data.get('password1') != cleaned_data.get('password2'):
            raise ValidationError('Passwords do not match!')
    
    def save(self, commit=True):
        user = super(SignUpForm, self).save(commit=False)
        user.is_active = False
        if commit:
            user.save()
            author = Author.objects.create(user=user,
                                displayName = self.cleaned_data.get('displayName'),
                                github = self.cleaned_data.get('github'))
            author.save()
            
        return user


class DateInput(forms.DateInput):
    input_type= 'date'
    


col12 = 'form-group col-md-12 mb-2'
submit = 'text-center mt-2 mb-2 btn btn-warning mt-3'
class EditProfileForm(forms.ModelForm):
    about = forms.CharField(required=False, widget=forms.Textarea(attrs={
            'rows' : 4,}))
    birthday = forms.DateField(required=False, widget=DateInput)
    class Meta:
        model = Author
        fields = ['displayName', 'github', 'birthday', 'email', 'about']
        widgets = {
            'categories': forms.Select(attrs={'rows': 1}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(  
            Row(
                Column('displayName', css_class=col12),
            ),
            Row(
                Column('github', css_class=col12),
            ),
            Row(
                Column('birthday', css_class=col12),
            ),
            Row(
                Column('email', css_class=col12),
            ),
            Row(
                Column('about', css_class=col12),
               
            ),
            Submit('submit', 'Edit Profile', css_class=submit)
        )

    