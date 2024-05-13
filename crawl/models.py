from django.db import models

# Create your models here.
class ScrapeResult(models.Model):
    request_id = models.CharField(max_length=255)
    url = models.URLField()
    title = models.CharField(max_length=255)
    links = models.TextField()
    summary = models.TextField(default='No summary available')
