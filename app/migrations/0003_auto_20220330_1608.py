# Generated by Django 3.0.5 on 2022-03-30 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_auto_20220330_1606'),
    ]

    operations = [
        migrations.AlterField(
            model_name='test',
            name='result',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='test',
            name='status',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]