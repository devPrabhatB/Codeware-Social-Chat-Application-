import re
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Room, User

class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['name', 'username', 'password1', 'password2']

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not re.match(r'^[A-Za-z]{3,}$', name):
            raise ValidationError("Name must contain at least 3 letters and no numbers.")
        return name

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not re.match(r'^[A-Za-z0-9]{3,}$', username):
            raise ValidationError("Username must contain at least 3 characters, letters and numbers only.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise ValidationError("Enter a valid email address.")
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        password_regex = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        if not re.match(password_regex, password):
            raise ValidationError(
                "Password must be at least 8 characters long, contain a capital letter, a lowercase letter, a number, and a special character."
            )
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords do not match.")
        
        return cleaned_data


class RoomForm(ModelForm):
    class Meta:
        model = Room
        fields = '__all__'
        exclude = ['host', 'participants']

class UserForm(ModelForm):
    class Meta:
        model = User
        fields = [ 'avatar', 'name', 'username', 'email', 'bio']