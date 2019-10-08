from django.db import models


class Ambiguous(models.Model):
    name = models.CharField(max_length=20)
