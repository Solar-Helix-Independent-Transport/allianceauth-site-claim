# Generated by Django 4.0.10 on 2023-04-27 10:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('eveonline', '0017_alliance_and_corp_names_are_not_unique'),
        ('siteclaim', '0003_siteclaimconfiguration_valid_site_regions'),
    ]

    operations = [
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('found_by_discord', models.CharField(blank=True, default='', max_length=200)),
                ('found_by_discord_uid', models.BigIntegerField(blank=True, default=None, null=True)),
                ('claimed_by_discord', models.CharField(blank=True, default='', max_length=200)),
                ('claimed_by_discord_uid', models.BigIntegerField(blank=True, default=None, null=True)),
                ('run_by_us', models.BooleanField(blank=True, default=False)),
                ('run_by_notified_by_discord', models.CharField(blank=True, default='', max_length=200)),
                ('run_by_notified_by_discord_uid', models.BigIntegerField(blank=True, default=None, null=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('message_id', models.BigIntegerField(blank=True, default=None, null=True)),
                ('interaction_id', models.CharField(max_length=100)),
                ('system_provided', models.CharField(max_length=100)),
                ('site_id', models.CharField(max_length=25)),
                ('claimed_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sites_claimed', to='eveonline.evecharacter')),
                ('found_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sites_found', to='eveonline.evecharacter')),
                ('run_by_notified_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sites_notified', to='eveonline.evecharacter')),
                ('system', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='siteclaim.system')),
            ],
        ),
    ]
