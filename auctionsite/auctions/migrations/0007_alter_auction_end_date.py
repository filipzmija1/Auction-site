# Generated by Django 4.2 on 2023-05-06 08:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0006_auction_end_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auction',
            name='end_date',
            field=models.DateTimeField(),
        ),
    ]
