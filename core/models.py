from django.db import models

# Create your models here.

# JSON schema for an alert
class Alert(models.Model):
    external_id = models.CharField(max_length=50)
    date = models.DateField()
    title = models.TextField()
    regions = models.JSONField(default=list)
    diseases = models.JSONField(default=list)
    species = models.JSONField(default=list)
    locations = models.JSONField(default=list)

    def __str__(self):
        return f"{self.external_id} - {self.title[:50]}"