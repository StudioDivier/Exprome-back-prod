# Generated by Django 3.1.2 on 2020-11-16 07:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_auto_20201116_0737'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orders',
            name='by_time',
            field=models.TimeField(default='07:39'),
        ),
    ]
