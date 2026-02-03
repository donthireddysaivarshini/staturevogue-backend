from django.db import models
from django.utils.text import slugify
from django.db.models import Avg, Sum
from django.conf import settings

# --- 1. CORE CONFIGURATION ---
class Color(models.Model):
    name = models.CharField(max_length=50)  # e.g. "Navy"
    hex_code = models.CharField(max_length=7)  # e.g. "#1F2B5B"

    def __str__(self):
        return self.name

class Size(models.Model):
    name = models.CharField(max_length=10)  # S, M, L, XL, 32
    sort_order = models.IntegerField(default=0)  # 1, 2, 3...

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.name

# --- 2. CATEGORIES (The "Shop By Collection" Grid) ---
class Category(models.Model):
    # Categories can be specific to a gender or apply to "All" (Both)
    GENDER_OPTIONS = (('Men', 'Men'), ('Women', 'Women'), ('All', 'All'))

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    description = models.TextField(blank=True)
    
    # 🔥 NEW: Gender field for Categories
    gender = models.CharField(max_length=10, choices=GENDER_OPTIONS, default='All')
    
    is_featured = models.BooleanField(default=False) 

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.gender})"

# --- 3. CURATED COLLECTIONS (The "Most Popular" / "Gym Fit" Groups) ---
class Collection(models.Model):
    GENDER_OPTIONS = (('Men', 'Men'), ('Women', 'Women'), ('All', 'All'))

    title = models.CharField(max_length=100)  # e.g. "Gym Fit", "Travel Wear"
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to='collections/', help_text="Cover image for this collection")
    description = models.TextField(blank=True)
    
    # 🔥 NEW: Gender field for Collections
    gender = models.CharField(max_length=10, choices=GENDER_OPTIONS, default='All')
    
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.gender})"

# --- 4. THE PRODUCT ---
class Product(models.Model):
    # 🔥 UPDATED: Removed 'Unisex'
    GENDER_CHOICES = (('Men', 'Men'), ('Women', 'Women'))
    
    BADGE_CHOICES = (
        ('BESTSELLER', 'Bestseller'),
        ('NEW', 'New Arrival'),
        ('TRENDING', 'Trending'),
        ('SALE', 'On Sale'),
    )

    # Basic Info
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    
    # Relationships
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    collections = models.ManyToManyField(Collection, blank=True, related_name='products')

    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Details
    fabric = models.CharField(max_length=100, blank=True)
    fit = models.CharField(max_length=100, blank=True)
    features = models.TextField(help_text="Enter features on new lines")
    care_instructions = models.TextField(help_text="Enter instructions on new lines")

    # Marketing
    badge = models.CharField(max_length=50, choices=BADGE_CHOICES, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    # --- DYNAMIC CALCULATIONS ---
    @property
    def in_stock(self):
        total = self.variants.aggregate(total=Sum('stock'))['total']
        return (total or 0) > 0

    @property
    def average_rating(self):
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0.0

    @property
    def review_count(self):
        return self.reviews.count()

# --- 5. IMAGES (Linked to Colors) ---
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, help_text="Link this image to a specific color variant")
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['id'] 

    def __str__(self):
        return f"{self.product.title} Image"

# --- 6. VARIANTS (SKU & Stock) ---
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    sku = models.CharField(max_length=100, unique=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('product', 'color', 'size')

    def save(self, *args, **kwargs):
        if not self.sku:
            # Auto-generate SKU: PRODID-COL-SIZ (e.g. 101-BLK-XL)
            self.sku = f"{self.product.id or 'NEW'}-{self.color.name[:3].upper()}-{self.size.name}".upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.title} - {self.color.name}/{self.size.name}"

# --- 7. REVIEWS ---
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=100)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    purchased_variant = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rating}* - {self.product.title}"

class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    usage_limit = models.IntegerField(default=100)
    uses_count = models.IntegerField(default=0)

    def __str__(self):
        return self.code

class SiteConfig(models.Model):
    shipping_flat_rate = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    shipping_free_above = models.DecimalField(max_digits=10, decimal_places=2, default=2000.00)
    tax_rate_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=18.00) 
    cod_extra_fee = models.DecimalField(max_digits=10, decimal_places=2, default=50.00, help_text="Extra charge for Cash on Delivery")
    def __str__(self):
        return "Miscellaneous Charges Configuration"

    class Meta:
        verbose_name = "Miscellaneous Charges"
        verbose_name_plural = "Miscellaneous Charges"