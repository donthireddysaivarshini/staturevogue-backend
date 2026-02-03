from django.db import models

class AnnouncementBar(models.Model):
    text = models.CharField(max_length=255, help_text="Text to display on top bar")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.text

class HeroSlide(models.Model):
    image = models.ImageField(upload_to='hero/')
    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=200)
    button_text = models.CharField(max_length=50, default="SHOP NOW")
    button_link = models.CharField(max_length=200, default="/products")
    order = models.IntegerField(default=0, help_text="Order of display")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

class BrandStory(models.Model):
    heading = models.CharField(max_length=100, default="OUR STORY")
    content = models.TextField()
    image_1 = models.ImageField(upload_to='brand/', help_text="First image (Men)")
    image_2 = models.ImageField(upload_to='brand/', help_text="Second image (Women)")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Brand Story"

    def __str__(self):
        return self.heading

class BrandFeature(models.Model):
    """ The Icons under the story """
    title = models.CharField(max_length=50, help_text="e.g. On the move")
    icon_image = models.ImageField(upload_to='icons/', help_text="Upload a small SVG or PNG icon (white color preferred)")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title