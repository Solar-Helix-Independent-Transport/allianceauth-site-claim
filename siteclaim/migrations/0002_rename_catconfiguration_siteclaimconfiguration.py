# Generated by Django 4.0.10 on 2023-04-27 08:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('siteclaim', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='CATConfiguration',
            new_name='SiteClaimConfiguration',
        ),
    ]
