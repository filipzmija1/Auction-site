# Generated by Django 4.2 on 2023-05-19 18:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0019_alter_item_image'),
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
