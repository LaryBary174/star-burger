# Generated by Django 5.1.6 on 2025-03-13 14:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0039_orderitem_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('unprocessed', 'необработанный'), ('on kitchen', 'на кухне'), ('on the way', 'в пути'), ('delivered', 'доставлен')], db_index=True, default='unprocessed', max_length=50, verbose_name='статус заказа'),
        ),
    ]
