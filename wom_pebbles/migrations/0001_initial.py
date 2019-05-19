# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-05-19 19:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Reference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(max_length=255, unique=True)),
                ('title', models.CharField(max_length=150)),
                ('description', models.TextField(blank=True, default=b'')),
                ('pub_date', models.DateTimeField(verbose_name=b'date published')),
                ('pin_count', models.IntegerField(default=0)),
                ('sources', models.ManyToManyField(related_name='productions', to='wom_pebbles.Reference')),
            ],
        ),
    ]
