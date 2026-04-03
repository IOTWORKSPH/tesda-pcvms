# users/forms_user_management.py

from django import forms
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from .models import User, Entity


# ==========================================================
# SYSTEM ADMIN – CREATE ENTITY + ADMINISTRATOR
# ==========================================================

class EntityCreateForm(forms.ModelForm):

    class Meta:
        model = Entity
        fields = ["code", "name", "address", "tin"]

    def clean_code(self):
        code = self.cleaned_data["code"].upper()

        if Entity.objects.filter(code=code).exists():
            raise ValidationError("Entity code already exists.")

        return code


class AdministratorCreateForm(forms.ModelForm):

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "employee_number",
            "position",
            "designation",
            "office",
        ]

    def clean_username(self):
        username = self.cleaned_data["username"]

        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists.")

        return username

    def clean_employee_number(self):
        emp_no = self.cleaned_data["employee_number"]

        if User.objects.filter(employee_number=emp_no).exists():
            raise ValidationError("Employee number already exists.")

        return emp_no


# ==========================================================
# ENTITY ADMIN – CREATE USERS WITH ROLE
# ==========================================================

ROLE_CHOICES = [
    ("Staff", "Staff"),
    ("Custodian", "Custodian"),
    ("Inspection", "Inspection"),
    ("Supply", "Supply"),
]


class UserCreateForm(forms.ModelForm):

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "employee_number",
            "position",
            "designation",
            "office",
            "role",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "employee_number": forms.TextInput(attrs={"class": "form-control"}),
            "position": forms.TextInput(attrs={"class": "form-control"}),
            "designation": forms.TextInput(attrs={"class": "form-control"}),
            "office": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_username(self):
        username = self.cleaned_data["username"]

        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists.")

        return username

    def clean_employee_number(self):
        emp_no = self.cleaned_data["employee_number"]

        if User.objects.filter(employee_number=emp_no).exists():
            raise ValidationError("Employee number already exists.")

        return emp_no