from django.db import models

class Phone_sel(models.Model):
    """Phone product parsed from brain.com.ua."""

    # Main data
    full_product_name = models.CharField(max_length=255, null=True )
    color = models.CharField(max_length=100, null=True )
    memory_size = models.CharField(max_length=100, null=True )
    manufacturer = models.CharField(max_length=100, null=True )
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    discounted_price = models.DecimalField(max_digits=12, decimal_places=2, null=True,
                                           blank=True)
    product_code = models.CharField(max_length=100, null=True )
    reviews_count = models.IntegerField(null=True )
    screen_diagonal = models.CharField(max_length=50, null=True )
    display_resolution = models.CharField(max_length=100, null=True )

    # Additional data
    photos = models.JSONField(default=list, null=True, blank=True )
    specifications = models.JSONField(default=dict, null=True, blank=True )

    # Service fields
    link = models.URLField(max_length=500, null=True, unique=True )
    status = models.CharField(max_length=50, default="New", null=True)

    def __str__(self):
        return self.full_product_name or f"Phone #{self.pk}"
from django.db import models

# Create your models here.
