# Generated by Django 4.0.2 on 2023-06-24 08:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0029_alter_auction_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auction',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]