# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_pub', models.DateField(auto_now_add=True)),
                ('date_pub_edited', models.DateField(auto_now=True)),
                ('title', models.CharField(max_length=255)),
                ('body', models.TextField()),
            ],
        ),
    ]
