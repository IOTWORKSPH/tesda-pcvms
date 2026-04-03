#forms.py

from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from decimal import Decimal

from .models import (
    PettyCashVoucher,
    PCVItem,
)


# ==========================================================
# CASH ADVANCE FORM
# ==========================================================

class CashAdvanceForm(forms.ModelForm):

    class Meta:
        model = PettyCashVoucher
        fields = [
            "fund",
            "expense_category",
            "purpose",
            "amount_requested",
        ]

        widgets = {
            "fund": forms.Select(attrs={"class": "form-control"}),
            "expense_category": forms.Select(attrs={"class": "form-control"}),
            "purpose": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),
            "amount_requested": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01"
            }),
        }

    # ======================================================
    # INITIALIZATION
    # ======================================================

    def __init__(self, *args, **kwargs):

        user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        if user and user.entity:

            # 🔐 SHOW ONLY FUNDS IN USER ENTITY
            funds = user.entity.funds.filter(is_active=True)

            self.fields["fund"].queryset = funds

            # 🔐 SHOW ONLY ENTITY EXPENSE CATEGORIES
            self.fields["expense_category"].queryset = (
                user.entity.expense_categories.filter(is_active=True)
            )

            # ⭐ AUTO SELECT DEFAULT FUND
            if not self.instance.pk:

                default_fund = funds.first()

                if default_fund:
                    self.fields["fund"].initial = default_fund

        # 🔒 LOCK FORM IF NOT DRAFT
        if self.instance.pk and self.instance.status != "DRAFT":

            for field in self.fields:
                self.fields[field].disabled = True


    # ======================================================
    # VALIDATION
    # ======================================================

    def clean_amount_requested(self):

        amount = self.cleaned_data.get("amount_requested")

        if amount is None or amount <= Decimal("0.00"):
            raise forms.ValidationError(
                "Amount must be greater than zero."
            )

        return amount


# ==========================================================
# REFUND / REIMBURSEMENT FORM
# ==========================================================


class RefundForm(forms.ModelForm):

    # Editable Supplier Field (Text Input)
    supplier_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter supplier name exactly as shown on receipt"
        })
    )

    purchase_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": "form-control"
        })
    )

    class Meta:
        model = PettyCashVoucher
        fields = [
            "purchase_date",
            "purpose",
            "expense_category",
            "fund",
            "official_receipt_number",
        ]

        widgets = {
            "purpose": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),
            "expense_category": forms.Select(attrs={
                "class": "form-control"
            }),
            "fund": forms.Select(attrs={
                "class": "form-control"
            }),
            "official_receipt_number": forms.TextInput(attrs={
                "class": "form-control"
            }),
        }

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(self, *args, **kwargs):

        user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        if user and user.entity:

            funds = user.entity.funds.filter(is_active=True)

            # 🔐 SHOW ONLY ENTITY FUNDS
            self.fields["fund"].queryset = funds

            # ⭐ AUTO SELECT FIRST FUND
            if not self.instance.pk:
                default_fund = funds.first()
                if default_fund:
                    self.fields["fund"].initial = default_fund

            # 🔐 ENTITY EXPENSE CATEGORIES
            self.fields["expense_category"].queryset = (
                user.entity.expense_categories.filter(is_active=True)
            )

        # Populate supplier if editing
        if self.instance.pk and self.instance.supplier:
            self.fields["supplier_name"].initial = self.instance.supplier.name

        # 🔒 LOCK IF NOT DRAFT
        if self.instance.pk and self.instance.status != "DRAFT":
            for field in self.fields:
                self.fields[field].disabled = True

    # ==========================================================
    # VALIDATION
    # ==========================================================

    def clean(self):
        cleaned_data = super().clean()

        purchase_date = cleaned_data.get("purchase_date")
        supplier_name = cleaned_data.get("supplier_name")
        receipt_no = cleaned_data.get("official_receipt_number")

        if not purchase_date:
            raise forms.ValidationError("Purchase date is required.")

        if not supplier_name:
            raise forms.ValidationError("Supplier name is required.")

        if not receipt_no:
            raise forms.ValidationError("Official receipt number is required.")

        return cleaned_data


# ==========================================================
# LINE ITEM FORM
# ==========================================================

class PCVItemForm(forms.ModelForm):

    class Meta:
        model = PCVItem
        fields = [
            "description",
            "unit",
            "quantity",
            "unit_cost",
        ]

        widgets = {
            "description": forms.TextInput(attrs={
                "class": "form-control",
                "required": True
            }),
            "unit": forms.TextInput(attrs={
                "class": "form-control",
                "required": True
            }),
            "quantity": forms.NumberInput(attrs={
                "class": "form-control qty",
                "step": "0.01",
                "min": "0.01",
                "required": True
            }),
            "unit_cost": forms.NumberInput(attrs={
                "class": "form-control unit-cost",
                "step": "0.01",
                "min": "0.01",
                "required": True
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        description = cleaned_data.get("description")
        unit = cleaned_data.get("unit")
        qty = cleaned_data.get("quantity")
        cost = cleaned_data.get("unit_cost")

        # 🚨 Strict required validation
        if not description:
            raise forms.ValidationError("Description is required.")

        if not unit:
            raise forms.ValidationError("Unit is required.")

        if qty is None:
            raise forms.ValidationError("Quantity is required.")

        if cost is None:
            raise forms.ValidationError("Unit cost is required.")

        if qty <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")

        if cost <= 0:
            raise forms.ValidationError("Unit cost must be greater than zero.")

        return cleaned_data



class BasePCVItemFormSet(BaseInlineFormSet):

    def clean(self):
        super().clean()

        if any(self.errors):
            return

        valid_forms = 0

        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                valid_forms += 1

        if valid_forms == 0:
            raise forms.ValidationError(
                "At least one expense item is required."
            )

PCVItemFormSet = inlineformset_factory(
    PettyCashVoucher,
    PCVItem,
    form=PCVItemForm,
    formset=BasePCVItemFormSet,
    extra=1,
    can_delete=False,
    min_num=1,
    validate_min=True
)
