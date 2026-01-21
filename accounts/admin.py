from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .models import SavedAddress

# Define how the user looks in the Admin Panel
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'first_name', 'phone', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'phone', 'password'),
        }),
    )
    search_fields = ('email', 'first_name', 'phone')
    ordering = ('email',)

# Register the model
admin.site.register(CustomUser, CustomUserAdmin)


@admin.register(SavedAddress)
class SavedAddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'label', 'first_name', 'last_name', 'city', 'zip_code', 'phone', 'is_default', 'created_at')
    list_filter = ('is_default', 'city', 'state', 'country')
    search_fields = ('user__email', 'label', 'first_name', 'last_name', 'address', 'city', 'zip_code', 'phone')
    ordering = ('-is_default', '-created_at')
    readonly_fields = ('created_at',)