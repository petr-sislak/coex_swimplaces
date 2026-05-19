from django.db import models


class SwimPlace(models.Model):
    external_id = models.PositiveIntegerField(unique=True)
    import_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=120)
    rating = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    description = models.TextField(blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    address = models.CharField(max_length=255, blank=True)
    website_url = models.URLField(max_length=500, blank=True)
    dog_swimming = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["-rating"]),
            models.Index(fields=["dog_swimming"]),
        ]
        verbose_name = "swim place"
        verbose_name_plural = "swim places"

    def __str__(self) -> str:
        return self.name
