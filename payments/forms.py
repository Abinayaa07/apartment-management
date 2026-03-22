from django import forms

from accounts.models import User

from .models import Payment


class AssignPaymentForm(forms.ModelForm):
    resident = forms.ModelChoiceField(
        queryset=User.objects.filter(role="resident").order_by("username"),
        empty_label="Select resident",
    )

    class Meta:
        model = Payment
        fields = ["resident", "month", "year", "amount"]

