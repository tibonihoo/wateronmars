# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-31 21:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wom_pebbles', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reference',
            name='description',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='reference',
            name='pub_date',
            field=models.DateTimeField(verbose_name='date published'),
        ),
    ]