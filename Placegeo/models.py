from django.db import models

# Create your models here.

class Place(models.Model):
    address = models.CharField('Адрес',max_length=100)
    latitude = models.FloatField('Широта',blank=True,null=True)
    longitude = models.FloatField('Долгота',blank=True,null=True)

    def __str__(self):
        return self.address
