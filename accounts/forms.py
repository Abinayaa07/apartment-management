from django import forms
from .models import FamilyMember, User
from django.contrib.auth.forms import UserCreationForm


class RegisterForm(UserCreationForm):

    email = forms.EmailField()
    id_proof = forms.FileField(required=False)
    address_proof = forms.FileField(required=False)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'phone',
            'block_name',
            'flat_number',
            'vehicle_number',
            'id_proof',
            'address_proof',
            'role',
            'password1',
            'password2'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = [
            choice for choice in self.fields["role"].choices if choice[0] != "admin"
        ]
        self.fields["role"].help_text = "Choose Resident, Security, or Staff. Admin accounts are created only by admin."
        self.fields["block_name"].help_text = "Example: A Block"
        self.fields["flat_number"].help_text = "Example: 102"
        self.fields["vehicle_number"].help_text = "Optional. Add your vehicle number if applicable."

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")

        if role == "resident":
            if not cleaned_data.get("id_proof"):
                self.add_error("id_proof", "Residents must upload an ID proof.")
            if not cleaned_data.get("address_proof"):
                self.add_error("address_proof", "Residents must upload an address proof.")

        return cleaned_data


class FamilyMemberForm(forms.ModelForm):
    class Meta:
        model = FamilyMember
        fields = [
            "member_name",
            "gender",
            "relationship",
            "date_of_birth",
            "kyc_document",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["member_name"].help_text = "Enter the full name of the family or household member."
        self.fields["relationship"].help_text = "Example: Self, Father, Mother, Sister, Son."
        self.fields["date_of_birth"].widget = forms.DateInput(attrs={"type": "date"})
