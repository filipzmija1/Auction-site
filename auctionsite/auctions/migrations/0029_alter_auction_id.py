# Generated by Django 4.0.2 on 2023-06-24 08:26

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0028_alter_auction_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auction',
            name='id',
            field=models.UUIDField(default=uuid.uuid3, editable=False, primary_key=True, serialize=False, unique=True),
        ),
    ]
