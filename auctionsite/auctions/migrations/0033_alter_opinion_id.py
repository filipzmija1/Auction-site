# Generated by Django 4.0.2 on 2023-06-24 17:56

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0032_alter_auction_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='opinion',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True),
        ),
    ]
