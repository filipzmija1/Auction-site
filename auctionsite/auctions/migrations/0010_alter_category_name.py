# Generated by Django 4.2 on 2023-05-07 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0009_alter_opinion_date_edited'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.SlugField(max_length=64),
        ),
    ]
