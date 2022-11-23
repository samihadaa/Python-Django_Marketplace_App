from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.http import HttpResponse
from .models import Product,OrderDetail
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.generic import ListView,DetailView,TemplateView
from django.views.generic.edit import CreateView,UpdateView,DeleteView
from django.urls import reverse,reverse_lazy
from django.http.response import HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json
import stripe
# Create your views here.
def index(request):
    return HttpResponse("Hello World")

# This is a function method for showing product list
def products(request):
    products = Product.objects.all()
    context = {'products':products}
    return render(request,'my_app/index.html',context)

# Using Class based view for above product view (ListView)
class ProductListView(ListView):
    model = Product
    template_name = 'my_app/index.html'
    context_object_name = 'products'
    paginate_by = 6

#This is a function method for showing product details
def product_detail(request,id):
    product = Product.objects.get(id = id)
    context = {'product':product}
    return render(request,'my_app/detail.html',context)

#Using Class based view for above product Detail view (DetailView)
class ProductDetailView(DetailView): 
    model = Product
    template_name = 'my_app/detail.html'
    context_object_name = 'product'
    pk_url_kwarg = 'pk'
    
#adding publish key to the context 
    def get_context_data(self, **kwargs):
        context = super(ProductDetailView,self).get_context_data(**kwargs)
        context['stripe_publishable_key'] = settings.STRIPE_PUBLISHABLE_KEY
        return context

#  This is a function method for adding products to the productView
#Authentification needed t have access to addin product page
@login_required
def add_product(request):
    if request.method =='POST':
        seller_name = request.user
        name = request.POST.get('name')
        price = request.POST.get('price')
        desc = request.POST.get('desc')
        image = request.FILES['upload']
        product = Product(name=name,price=price,desc=desc,image=image,seller_name=seller_name)
        product.save()
    return render(request,'my_app/add_product.html')

#class based view for creating a product
class ProductCreateView(CreateView):
    model = Product
    fields = ['name','price','desc','image','seller_name']

def update_product(request,id):
    product = Product.objects.get(id=id)
    context = {'product':product,}
    if request.method=='POST':
        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        product.desc = request.POST.get('desc')
        product.image = request.FILES['upload']
        product.save()
        return redirect('/my_app/products')
    return render(request,'my_app/update_product.html',context)

#Class based view for updating a product
#I will use the previous function update_product to render this view
class ProductUpdateView(UpdateView):
    model = Product
    fields = ['name','price','desc','image','seller_name']
    template_name_suffix = 'update_form'

def delete_product(request,id):
    product = Product.objects.get(id=id)
    context = {'product':product}
    if request.method == 'POST':
        product.delete()
        return redirect('/my_app/products')
    return render(request,'my_app/delete_product.html',context)

#Class based delete view
class ProductDelete(DeleteView):
    model = Product

def my_listings(request):
    products = Product.objects.filter(seller_name=request.user)
    context= {
        'products': products,
    }
    return render(request,'my_app/mylistings.html',context)

@csrf_exempt
def create_checkout_session(request,id):
    product = get_object_or_404(Product,pk=id)
    stripe.api_key = settings.STRIPE_SECRET_KEY
    checkout_session = stripe.checkout.Session.create(
        customer_email = request.user.email,
        payment_method_types = ['card'],
        line_items = [
            {
                'price_data':{
                    'currency': 'usd',
                    'product_data':{
                        'name':product.name,
                    },
                    'unit_amount': int(product.price * 100),
                },
                'quantity': 1,
            }
        ],
        mode = 'payment',
        success_url = request.build_absolute_uri(reverse('my_app:success')) + "?session_id = {CHECKOUT_SESSION_ID}",
        cancel_url = request.build_absolute_uri(reverse('my_app:failed'))
    )
    order = OrderDetail()
    order.customer_username = request.user.username
    order.product = Product
    order.stripe_payment_intent = checkout_session['payment_intent']
    order.amount = int(product.price*100)
    order.save()
    return JsonResponse({'sessionId':checkout_session})

class PaymentSuccessView(TemplateView):
    tempate_name = 'my_app/payment_success.html'

    def get(self,request,*args,**kwargs):
        session_id = request.GET.get('session_id')
        if session_id is None:
            return HttpResponseNotFound()
 
        stripe.checkout.Session.retrieve(session_id)
        stripe.api_key = settings.STRIPE_SECRET_KEY
        order = get_object_or_404(OrderDetail,stripe_payment_intent = session.payment_intent)
        order.has_paid = True
        order.save()
        return render(request,self.tempate_name)
    
class PaymentFailedView(TemplateView):
    template_name = 'my_app/payment_failed.html'