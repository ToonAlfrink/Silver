from django.db import models
from django.core.exceptions import ObjectDoesNotExist

class Word(models.Model):
    word = models.CharField(max_length = 140)
    count = models.IntegerField()
    date = models.DateField()
    class Meta:
        unique_together = ("word", "date")

class StockDay(models.Model):
    opening = models.IntegerField(null = True, blank = True)
    closing = models.IntegerField(null = True, blank = True)
    date = models.DateField()

    @classmethod
    def get_or_create(cls, date, **kwargs):
        try:
            obj = cls.objects.get(date = date, **kwargs)
        except ObjectDoesNotExist:
            obj = cls(date = date, **kwargs)
        return obj
