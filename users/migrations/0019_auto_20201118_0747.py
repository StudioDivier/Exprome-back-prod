# Generated by Django 3.1.2 on 2020-11-18 07:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0018_auto_20201118_0746'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orders',
            name='by_time',
            field=models.TimeField(default='07:47'),
        ),
    ]
