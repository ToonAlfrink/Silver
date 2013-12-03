from django.db import models

class Word(models.Model):
    word = models.CharField(max_length = 140)
    count = models.IntegerField()
    date = models.DateField()
    class Meta:
        unique_together = ("word", "date")
