# Generated by Django 4.2 on 2023-05-19 18:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0021_remove_item_height_field_remove_item_width_field_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='height_field',
            field=models.IntegerField(default=200),
        ),
        migrations.AddField(
            model_name='item',
            name='width_field',
            field=models.IntegerField(default=200),
        ),
        migrations.AlterField(
            model_name='item',
            name='image',
            field=models.ImageField(blank=True, height_field='height_field', null=True, upload_to='images/', width_field='width_field'),
        ),
    ]
