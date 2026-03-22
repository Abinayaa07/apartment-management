from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_user_flat_number"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="address_proof",
            field=models.FileField(blank=True, null=True, upload_to="resident_docs/address_proofs/"),
        ),
        migrations.AddField(
            model_name="user",
            name="id_proof",
            field=models.FileField(blank=True, null=True, upload_to="resident_docs/id_proofs/"),
        ),
    ]
