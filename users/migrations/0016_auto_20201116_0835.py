# Generated by Django 3.1.2 on 2020-11-16 08:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_auto_20201116_0834'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orders',
            name='by_time',
            field=models.TimeField(default='08:35'),
        ),
        migrations.AlterField(
            model_name='orders',
            name='type',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]