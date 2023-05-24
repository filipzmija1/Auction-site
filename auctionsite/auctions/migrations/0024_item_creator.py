# Generated by Django 4.2 on 2023-05-24 07:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auctions', '0023_remove_item_height_field_remove_item_width_field_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
