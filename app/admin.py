from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, CharityApplication,Product, SellerProfile # <-- import from your models

# --- Custom User Admin ---
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'firstname', 'lastname', 'is_staff', 'is_superuser')
    search_fields = ('email', 'firstname', 'lastname')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('firstname', 'lastname', 'phone', 'address')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'firstname', 'lastname', 'phone', 'password1', 'password2'),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)

# --- Charity Application Admin ---
@admin.register(CharityApplication)
class CharityApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'is_approved')
    list_filter = ('is_approved',)
    search_fields = ('name', 'email', 'phone')

admin.site.register(Product)


from django.contrib import admin
from .models import SellerProfile, CustomUser

@admin.action(description="Approve selected sellers")
def approve_sellers(modeladmin, request, queryset):
    for seller in queryset:
        seller.is_approved = True
        seller.save()

        seller.user.status = True     # activate user
        seller.user.is_active = True
        seller.user.save()

from django.contrib import admin
from .models import SellerProfile

from django.contrib import admin
from .models import SellerProfile, CustomUser

@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user', 'is_approved')
    actions = ['approve_seller', 'reject_seller']

    def approve_seller(self, request, queryset):
        for seller in queryset:
            seller.is_approved = True
            seller.save()

            user = seller.user
            user.user_type = CustomUser.SELLER
            user.save()

        self.message_user(request, "Seller approved successfully") 
         

def reject_seller(self, request, queryset):
    # This updates the database for all selected sellers
    queryset.update(is_rejected=True, is_approved=False)
    
    # Optional: Update user type to standard user
    for seller in queryset:
        user = seller.user
        user.user_type = 'USER'
        user.save()

    self.message_user(request, "Selected sellers have been rejected.")

# @admin.register(SellerProfile)
# class SellerProfileAdmin(admin.ModelAdmin):
#     list_display = ('business_name', 'user', 'is_approved')
#     list_filter = ('is_approved', 'category')
#     actions = [approve_sellers]


from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at')
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity')
    list_filter = ('cart', 'product')


from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'created_at')
    inlines = [OrderItemInline]
