from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout as auth_logout
from django.contrib import messages
from app.models import CustomUser
from .models import Product


from .models import (
    CustomUser, CharityOption, CharityDonor, DonorApplication,
    CharityRequest, CharityApplication
)
from .forms import (
    MyUserCreationForm, LoginForm, MyPasswordResetForm,
    MySetPasswordForm, MyPasswordChangeForm,
    DonorApplicationForm, CharityRequestForm, CharityApplicationForm
)
from django.contrib.auth.views import (
    LoginView, PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test


# ----------------------------
# BASIC
# ----------------------------
def home(request):
    return render(request, "index.html")

def navbar(request):
    return render(request, "navbar.html")

def is_admin(user):
    return user.is_staff or user.is_superuser


# ----------------------------
# ADMIN DASHBOARD
# ----------------------------
@user_passes_test(is_admin)
def admin_dashboard(request):
    donors_pending = DonorApplication.objects.filter(approved=False).count()
    donors_approved = DonorApplication.objects.filter(approved=True).count()
    charities_pending = CharityRequest.objects.filter(approved=False).count()
    charities_approved = CharityRequest.objects.filter(approved=True).count()
    charity_apps_pending = CharityApplication.objects.filter(approved=False).count()
    charity_apps_approved = CharityApplication.objects.filter(approved=True).count()

    donors = DonorApplication.objects.all()
    charities = CharityRequest.objects.all()
    charity_apps = CharityApplication.objects.all()

    context = {
        "donors_pending": donors_pending,
        "donors_approved": donors_approved,
        "charities_pending": charities_pending,
        "charities_approved": charities_approved,
        "charity_apps_pending": charity_apps_pending,
        "charity_apps_approved": charity_apps_approved,
        "donors": donors,
        "charities": charities,
        "charity_apps": charity_apps,
    }
    return render(request, "admin_dashboard.html", context)


# ----------------------------
# USER REGISTRATION & LOGIN
# ----------------------------
def register_user(request, redirect_page):
    form = MyUserCreationForm()
    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email
            user.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect(redirect_page)
        else:
            messages.error(request, 'Error occurred during registration.')
    return render(request, 'user_reg.html', {'form': form})


def registration(request):
    return render(request, "register.html")


def user_reg(request):
    return register_user(request, 'normal_user_page')

def charity_user_reg(request):
    return register_user(request, 'charity_page')

def seller_reg(request):
    if request.method == 'POST':
        request.user.is_staff = True   # mark user as seller
        request.user.save()
        return redirect('seller_dashboard')
    return render(request, 'seller/seller_register.html')



from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse_lazy

class CustomLoginView(LoginView):
    template_name = 'login.html'
    form_class = LoginForm

    def form_invalid(self, form):
        messages.error(self.request, "Invalid email or password")
        return super().form_invalid(form)

    def get_success_url(self):
        user = self.request.user
        if user.user_type == CustomUser.SELLER:
            return reverse_lazy('seller_dashboard')
        elif user.user_type in [CustomUser.NORMAL, CustomUser.CHARITY]:
            return reverse_lazy('home')
        return reverse_lazy('home')


# ----------------------------
# PASSWORD MANAGEMENT
# ----------------------------
class CustomPasswordResetView(PasswordResetView):
    form_class = MyPasswordResetForm
    template_name = 'password_reset.html'
    success_url = reverse_lazy('password_reset_done')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = MySetPasswordForm
    template_name = 'password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'password_reset_complete.html'


def logout_view(request):
    auth_logout(request)
    return redirect('home')


# ----------------------------
# CHARITY PAGE & FORMS
# ----------------------------
def charity_page(request):
    options = CharityOption.objects.all()
    donors = CharityDonor.objects.all()

    options_with_progress = []
    for option in options:
        progress = (option.raised_amount / option.target_amount) * 100 if option.target_amount > 0 else 0
        options_with_progress.append({'option': option, 'progress': progress})

    context = {
        'options_with_progress': options_with_progress,
        'donors': donors
    }
    return render(request, 'charity_page.html', context)


def apply_donor(request):
    if request.method == "POST":
        donor_type = request.POST.get("donor_type")
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        reason = request.POST.get("reason")
        photo = request.FILES.get("photo")

        DonorApplication.objects.create(
            donor_type=donor_type,
            name=name,
            email=email,
            phone=phone,
            address=address,
            reason=reason,
            photo=photo
        )
        messages.success(request, "Your donor application has been submitted successfully!")
        return redirect("apply_donor")
    return render(request, "apply_doner.html")


def apply_charity(request):
    if request.method == 'POST':
        form = CharityRequestForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('charity_page')
    else:
        form = CharityRequestForm()
    return render(request, 'apply_charity.html', {'form': form})


def charity_application(request):
    if request.method == 'POST':
        form = CharityApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return render(request, 'charity_success.html')
    else:
        form = CharityApplicationForm()
    return render(request, 'charity_application.html', {'form': form})


# ----------------------------
# ADMIN APPROVAL HANDLERS
# ----------------------------

# Charity Request (basic)
@user_passes_test(is_admin)
def approve_charity_request(request, pk):
    charity = get_object_or_404(CharityRequest, pk=pk)
    charity.approved = True
    charity.save()
    messages.success(request, f"{charity.name} charity request approved.")
    return redirect("admin_dashboard")

@user_passes_test(is_admin)
def reject_charity_request(request, pk):
    charity = get_object_or_404(CharityRequest, pk=pk)
    charity.delete()
    messages.error(request, f"{charity.name}'s charity request rejected.")
    return redirect("admin_dashboard")


# Charity Application (new)
@user_passes_test(is_admin)
def approve_charity_app(request, pk):
    charity = get_object_or_404(CharityApplication, pk=pk)
    charity.approved = True
    charity.save()
    messages.success(request, f"Charity application by {charity.name} approved.")
    return redirect("admin_dashboard")

@user_passes_test(is_admin)
def reject_charity_app(request, pk):
    charity = get_object_or_404(CharityApplication, pk=pk)
    charity.delete()
    messages.error(request, f"Charity application by {charity.name} rejected.")
    return redirect("admin_dashboard")


# Donor Applications
@user_passes_test(is_admin)
def approve_donor(request, pk):
    donor = get_object_or_404(DonorApplication, pk=pk)
    donor.approved = True
    donor.save()
    messages.success(request, f"{donor.name} approved as donor.")
    return redirect("admin_dashboard")

@user_passes_test(is_admin)
def reject_donor(request, pk):
    donor = get_object_or_404(DonorApplication, pk=pk)
    donor.delete()
    messages.error(request, f"{donor.name}'s donor application rejected.")
    return redirect("admin_dashboard")

def charity_requests_list(request):
    pass


#E-Commerce Module

# def product_list(request):
#     return render(request,"shopping/list_product.html")


# from django.shortcuts import render, redirect
# from .forms import ProductForm
# from django.contrib.auth.decorators import login_required

# @login_required
# def add_product(request):
#     if request.method == 'POST':
#         form = ProductForm(request.POST, request.FILES)
#         if form.is_valid():
#             product = form.save(commit=False)
#             product.created_by = request.SELLER   # 👈 who added
#             product.save()
#             return redirect('product_list')
#     else:
#         form = ProductForm()
#     return render(request, 'shopping/add_product.html', {'form': form})

#     if not request.user.is_staff:
#         return redirect('home')

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import SellerProfile, CustomUser




@login_required
def seller_register(request):

    # Already approved seller
    if request.user.user_type == CustomUser.SELLER and request.user.status:
        return redirect('seller_dashboard')

    if request.method == 'POST':
        seller, created = SellerProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'business_name': request.POST.get('business_name'),
                'tax_id': request.POST.get('tax_id'),
                'category': request.POST.get('category'),
            }
        )

        # If already exists → just go to pending
        if not created:
            return redirect('seller_pending')

        request.user.user_type = CustomUser.SELLER
        request.user.status = False
        request.user.save()

        return redirect('seller_pending')

    return render(request, 'seller/seller_register.html')



@login_required
def seller_dashboard(request):
    seller = request.user.seller_profile

    # 1. Check rejection FIRST
    if seller.is_rejected:
        return redirect('seller_rejected')

    # 2. Check if they are still pending
    if not seller.is_approved:
        return redirect('seller_pending')

    # 3. If neither, show dashboard
    return render(request, 'seller/dashboard.html')

@login_required
def seller_entry(request):
    seller = request.user.seller_profile

    # Always check rejection as the priority
    if seller.is_rejected:
        return redirect('seller_rejected')

    if not seller.is_approved:
        return redirect('seller_pending')

    return redirect('seller_dashboard')

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.http import HttpResponse




@login_required
def seller_rejected(request):
    seller = request.user.seller_profile
    return HttpResponse(f"REJECTED ❌<br>Reason: {seller.rejection_reason}")

@login_required
def seller_pending(request):
    try:
        seller = request.user.seller_profile
        seller.refresh_from_db()
    except Exception:
        return redirect('seller_dashboard')  # ✅ FIX

    # If approved → dashboard
    if seller.is_approved:
        if seller.is_rejected:
            seller.is_rejected = False
            seller.rejection_reason = ""
            seller.save()
        return redirect('seller_dashboard')

    return render(request, 'seller/seller_pending.html', {'seller': seller})


def approve_seller(self, request, queryset):
    for seller in queryset:
        seller.is_approved = True
        seller.is_rejected = False
        seller.rejection_reason = ''
        seller.save()

        user = seller.user
        user.user_type = 'SELLER'
        user.save()

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Product

@login_required
def add_product(request):
    if request.user.user_type != CustomUser.SELLER:
        return redirect('home')

    if request.method == 'POST':
        Product.objects.create(
            name=request.POST.get('name'),
            price=request.POST.get('price'),
            description=request.POST.get('description'),
            stock=request.POST.get('stock'),
            image=request.FILES.get('image'),
            created_by=request.user
        )
        return redirect('seller_dashboard')

    return render(request, 'seller/add_product.html')


@login_required
def my_products(request):
    if request.user.user_type != CustomUser.SELLER:
        return redirect('home')

    products = Product.objects.filter(created_by=request.user)
    return render(request, 'seller/my_products.html', {'products': products})


from django.shortcuts import render, get_object_or_404, redirect
from .models import Product
from .forms import ProductForm # Assuming you use a ModelForm

def edit_product(request, pk):
    # Fetch the specific product or return 404
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_value():
            form.save()
            return redirect('my_products')
    else:
        form = ProductForm(instance=product)
        
    return render(request, 'add_product.html', {'form': form, 'edit_mode': True})

@login_required
def edit_product(request, product_id):
    if request.user.user_type != CustomUser.SELLER:
        return redirect('home')

    product = get_object_or_404(
        Product,
        id=product_id,
        created_by=request.user
    )

    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock')
        product.description = request.POST.get('description')

        if request.FILES.get('image'):
            product.image = request.FILES.get('image')

        product.save()
        return redirect('my_products')

    return render(request, 'seller/edit_product.html', {'product': product})


@login_required
def delete_product(request, product_id):
    if request.user.user_type != CustomUser.SELLER:
        return redirect('home')

    product = get_object_or_404(
        Product,
        id=product_id,
        created_by=request.user
    )

    product.delete()
    return redirect('my_products')

# views.py

from .models import Cart

def list_product(request):
    products = Product.objects.all().order_by('-created_at')

    cart_count = 0

    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.items.count()
        except Cart.DoesNotExist:
            cart_count = 0

    return render(request, 'shopping/list_product.html', {
        'products': products,
        'cart_count': cart_count
    })


from django.shortcuts import render, get_object_or_404
from .models import Product

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, 'shopping/product_details.html', {
        'product': product
    })


#cart
from django.shortcuts import redirect, render, get_object_or_404
from .models import Product

from django.shortcuts import render, redirect, get_object_or_404
from .models import Product

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Cart, CartItem, Product

from django.shortcuts import get_object_or_404, redirect
from .models import Cart, CartItem, Product
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect # Ensure this is at the top of your file

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from .models import Cart, CartItem, Product
from django.db.models import Sum

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    # RECALCULATE FOR THE HEADER
    total_qty = cart.items.aggregate(total=Sum('quantity'))['total'] or 0
    request.session['cart_count'] = total_qty 
    
    return redirect('cart')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Product # Make sure to import your model

from django.contrib.auth.decorators import login_required

@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_items = cart.items.all()

    total_price = sum(item.subtotal() for item in cart_items)

    return render(request, 'cart/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_count': cart_items.count()
    })

from .models import CartItem

from django.shortcuts import redirect, get_object_or_404
from .models import CartItem

from django.shortcuts import get_object_or_404, redirect

@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user
    )

    if request.method == "POST":
        action = request.POST.get('action')
        
        # 1. Handle the Plus/Minus Button Clicks
        if action == 'increase':
            cart_item.quantity += 1
            cart_item.save()
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete() # Remove item if quantity goes below 1
        
        # 2. Handle Manual Input (if any)
        else:
            quantity = int(request.POST.get('quantity', 1))
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()

    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart = cart_item.cart # Get reference to cart before deleting item
    cart_item.delete()

    # RECALCULATE FOR THE HEADER
    total_qty = cart.items.aggregate(total=Sum('quantity'))['total'] or 0
    request.session['cart_count'] = total_qty

    return redirect('cart')

from .models import Cart
from django.db.models import Sum

def cart_count_processor(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            count = cart.items.aggregate(total=Sum('quantity'))['total'] or 0
            return {'global_cart_count': count}
    return {'global_cart_count': 0}

#checkout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem
from .models import Cart, CartItem


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = cart.items.all()

    if not items.exists():
        return redirect('cart')

    total = sum(item.subtotal() for item in items)

    if request.method == 'POST':
        order = Order.objects.create(
            user=request.user,
            full_name=request.POST['full_name'],
            phone=request.POST['phone'],
            address=request.POST['address'],
            city=request.POST['city'],
            pincode=request.POST['pincode'],
            total_price=total
        )

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity
            )

            item.product.stock -= item.quantity
            item.product.save()

        items.delete()  # clear cart
        return redirect('order_success', order.id)

    return render(request, 'checkout.html', {
        'items': items,
        'total': total
    })


def order_success(request, order_id):
    order = Order.objects.get(id=order_id)
    return render(request, 'order_success.html', {'order': order})

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_orders.html', {'orders': orders})



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .models import Cart, CartItem, Order, OrderItem

@login_required
def checkout_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = cart.items.all()

    if not items.exists():
        return redirect('list_product')

    total_price = sum(item.subtotal() for item in items)

    if request.method == 'POST':
        order = Order.objects.create(
            user=request.user,
            full_name=request.POST['full_name'],
            phone=request.POST['phone'],
            address=request.POST['address'],
            city=request.POST['city'],
            pincode=request.POST['pincode'],
            total_price=total_price,
            status='Pending'
        )

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity
            )

        return redirect('payment', order_id=order.id)

    return render(request, 'cart/checkout.html', {
        'cart_items': items,
        'total_price': total_price
    })


from django.shortcuts import render
from django.conf import settings
import razorpay

client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

def payment_view(request, order_id):
    amount = 100  # ₹100 test

    order = client.order.create({
        "amount": amount * 100,  # paise
        "currency": "INR",
        "payment_capture": 1
    })

    context = {
        "order_id": order["id"],
        "amount": amount,
        "razorpay_key": settings.RAZORPAY_KEY_ID
    }
    return render(request, "payment/payment.html", context)


from django.http import HttpResponse

def payment_success(request):
    return HttpResponse("🎉 Payment Successful")

