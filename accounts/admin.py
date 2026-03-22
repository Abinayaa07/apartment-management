from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "role",
        "block_name",
        "flat_number",
        "vehicle_number",
        "is_approved",
        "id_proof_link",
        "address_proof_link",
    )
    list_filter = ("role", "is_approved")
    fieldsets = UserAdmin.fieldsets + (
        (
            "Apartment Details",
            {
                "fields": (
                    "role",
                    "phone",
                    "block_name",
                    "flat_number",
                    "vehicle_number",
                    "is_approved",
                    "id_proof",
                    "address_proof",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Apartment Details",
            {
                "fields": (
                    "email",
                    "role",
                    "phone",
                    "block_name",
                    "flat_number",
                    "vehicle_number",
                    "id_proof",
                    "address_proof",
                    "is_approved",
                )
            },
        ),
    )

    def id_proof_link(self, obj):
        if obj.id_proof:
            return format_html('<a href="{}" target="_blank">View ID Proof</a>', obj.id_proof.url)
        return "-"

    id_proof_link.short_description = "ID Proof"

    def address_proof_link(self, obj):
        if obj.address_proof:
            return format_html('<a href="{}" target="_blank">View Address Proof</a>', obj.address_proof.url)
        return "-"

    address_proof_link.short_description = "Address Proof"
