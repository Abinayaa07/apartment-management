from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_user_block_name_user_vehicle_number"),
    ]

    operations = [
        migrations.CreateModel(
            name="FamilyMember",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("member_name", models.CharField(max_length=120)),
                ("gender", models.CharField(choices=[("male", "Male"), ("female", "Female"), ("other", "Other")], max_length=10)),
                ("relationship", models.CharField(max_length=50)),
                ("date_of_birth", models.DateField()),
                ("kyc_document", models.FileField(blank=True, null=True, upload_to="resident_docs/family_kyc/")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "resident",
                    models.ForeignKey(
                        limit_choices_to={"role": "resident"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="family_members",
                        to="accounts.user",
                    ),
                ),
            ],
            options={"ordering": ["member_name"]},
        ),
    ]
