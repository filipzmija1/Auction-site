# Generated by Django 4.2 on 2023-05-06 17:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0007_alter_auction_end_date'),
    ]

    operations = [
        migrations.RenameField(
            model_name='opinion',
            old_name='date',
            new_name='date_created',
        ),
        migrations.AddField(
            model_name='opinion',
            name='date_edited',
            field=models.DateTimeField(null=True),
        ),
    ]
