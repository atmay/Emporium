import sys
from PIL import Image

from io import BytesIO

from django.db import models
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


def get_models_for_count(*model_names):
    return [models.Count(model_name) for model_name in model_names]


def get_product_url(obj, viewname):
    ct_model = obj.__class__._meta.model_name
    return reverse(viewname, kwargs={'ct_model': ct_model, 'slug': obj.slug})


class ResolutionErrorException(Exception):
    pass


class LatestProductsManager:

    # @staticmethod
    def get_products_for_main_page(self, *args, **kwargs):
        # можно указать, товары какой категории должны попасть в выдачу первыми
        with_respect_to = kwargs.get('with_respect_to')
        products = []
        ct_models = ContentType.objects.filter(model__in=args)
        for ct_model in ct_models:
            # вызываем родительский класс у контент тайп модели, берем последние 5 продуктов
            model_products = ct_model.model_class()._base_manager.all().order_by('-id')[:5]
            products.extend(model_products)
            # получаем список всех объектов модели товаров, которые будут выведены на главную
        if with_respect_to:
            ct_model = ContentType.objects.filter(model=with_respect_to)
            if ct_model.exists():
                if with_respect_to in args:
                    return sorted(
                        products,
                        key=lambda x: x.__class__._meta.model_name.startswith(with_respect_to),
                        reverse=True
                    )
        return products


class LatestProducts:
    objects = LatestProductsManager()


class CategoryManager(models.Manager):
    CATEGORY_NAME_COUNT_NAME = {
        'notebooks': 'notebook__count',
        'smartphones': 'smartphone__count'
    }

    def get_queryset(self):
        return super().get_queryset()

    def get_categories_for_sidebar(self):
        models = get_models_for_count('notebook', 'smartphone')
        qs = list(self.get_queryset().annotate(*models))
        data = [
            dict(name=c.name,
                 url=c.get_absolute_url(),
                 count=getattr(c, self.CATEGORY_NAME_COUNT_NAME[c.name]))
            for c in qs
        ]
        return data


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Category name')
    slug = models.SlugField(unique=True)
    objects = CategoryManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    # image resolution
    MIN_RESOLUTION = (10, 10)
    MAX_RESOLUTION = (800, 800)
    MAX_IMAGE_SIZE = 3145728  # 3 Mb in bytes

    # abstract class for product classes
    class Meta:
        abstract = True

    title = models.CharField(max_length=255, verbose_name='Product name')
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name='Product image', null=True)
    description = models.TextField(verbose_name='Description', null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Price')
    category = models.ForeignKey(Category, verbose_name='Category', on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def get_model_name(self):
        return self.__class__.__name__.lower()

    def save(self, *args, **kwargs):
        # restrictions for image size, width and height
        if self.image:
            image = self.image
            img = Image.open(image)
            min_width, min_height = self.MIN_RESOLUTION
            max_width, max_height = self.MAX_RESOLUTION
            if img.width < min_width or img.height < min_height:
                raise ResolutionErrorException("Image is too big")
            if img.width > max_width or img.height > max_height:
                raise ResolutionErrorException("Image is too small")
        if self.image:
            # cropping images that are too large
            image = self.image
            img = Image.open(image)
            new_img = img.convert('RGB')
            new_img_resized = new_img.resize((400, 400), Image.ANTIALIAS)
            file_stream = BytesIO()
            new_img_resized.save(file_stream, 'JPEG', quality=90)
            file_stream.seek(0)
            name = '{}.{}'.format(*self.image.name.split('.'))
            self.image = InMemoryUploadedFile(
                file_stream, 'ImageField', name, 'jpeg/image', sys.getsizeof(file_stream), None
            )
            super().save(*args, **kwargs)


class Notebook(Product):
    diagonal = models.CharField(max_length=255, verbose_name='Diagonal')
    display_type = models.CharField(max_length=255, verbose_name='Display type')
    processor_freq = models.CharField(max_length=255, verbose_name='Processor frequency')
    ram = models.CharField(max_length=255, verbose_name='RAM')
    video_card = models.CharField(max_length=255, verbose_name='Video card')
    battery_capacity = models.CharField(max_length=255, verbose_name='Battery capacity')

    def __str__(self):
        return '{}: {}'.format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')


class Smartphone(Product):
    diagonal = models.CharField(max_length=255, verbose_name='Diagonal')
    display_type = models.CharField(max_length=255, verbose_name='Display type')
    resolution = models.CharField(max_length=255, verbose_name='Screen resolution')
    battery_capacity = models.CharField(max_length=255, verbose_name='Battery capacity')
    ram = models.CharField(max_length=255, verbose_name='RAM')
    sd = models.BooleanField(default=True, verbose_name='SD card')
    sd_max_volume = models.CharField(
        max_length=255, null=True, blank=True, verbose_name='SD max volume'
    )
    camera_main = models.CharField(max_length=255, verbose_name='Main camera')
    camera_frontal = models.CharField(max_length=255, verbose_name='Frontal camera')

    def __str__(self):
        return '{}: {}'.format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')


class CartProduct(models.Model):
    user = models.ForeignKey('Customer', verbose_name='Customer', on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart', verbose_name='Cart', on_delete=models.CASCADE, related_name='related_products')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Total price')

    def __str__(self):
        return 'Cart product: {}'.format(self.content_object.title)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.content_object.price
        super().save(*args, **kwargs)


class Cart(models.Model):
    owner = models.ForeignKey('Customer', null=True, verbose_name='Owner', on_delete=models.CASCADE)
    products = models.ManyToManyField(CartProduct, blank=True, related_name='related_cart')
    total_products = models.PositiveIntegerField(default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Total price', default=0)
    in_order = models.BooleanField(default=False)
    for_anonymous_user = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

 
class Customer(models.Model):
    user = models.ForeignKey(User, verbose_name='User', on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name='Phone number', null=True, blank=True)
    address = models.CharField(max_length=255, verbose_name='Address', null=True, blank=True)
    orders = models.ManyToManyField('Order', related_name='related_customer', verbose_name="Customer's orders")

    def __str__(self):
        return 'Customer: {} {}'.format(self.user.first_name, self.user.last_name)


class Order(models.Model):
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_READY = 'is_ready'
    STATUS_COMPLETED = 'completed'

    DELIVERY_TYPE_SELF_PICK = 'self_pick'
    DELIVERY_TYPE_DELIVERY = 'delivery'

    STATUS_CHOICES = (
        (STATUS_NEW, 'New order'),
        (STATUS_IN_PROGRESS, 'Order in progress'),
        (STATUS_READY, 'Order is ready'),
        (STATUS_COMPLETED, 'Order completed')
    )

    DELIVERY_CHOICES = (
        (DELIVERY_TYPE_SELF_PICK, 'Self pick'),
        (DELIVERY_TYPE_DELIVERY, 'Delivery to address')
    )

    customer = models.ForeignKey(Customer,
                                 related_name='related_order',
                                 verbose_name='Customer',
                                 on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, verbose_name='First name')
    last_name = models.CharField(max_length=255, verbose_name='Last name')
    phone = models.CharField(max_length=255, verbose_name='Phone number')
    cart = models.ForeignKey(Cart, verbose_name='Cart', on_delete=models.CASCADE, null=True, blank=True)
    address = models.CharField(max_length=1024,
                               verbose_name='Address',
                               null=True,
                               blank=True)
    status = models.CharField(max_length=100,
                              verbose_name='Order status',
                              choices=STATUS_CHOICES,
                              default=STATUS_NEW)
    delivery_type = models.CharField(max_length=100,
                                     verbose_name='Delivery status',
                                     choices=DELIVERY_CHOICES,
                                     default=DELIVERY_TYPE_SELF_PICK)
    comment = models.TextField(verbose_name='Notes on the Order', blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True, verbose_name='Order created at')
    order_date = models.DateField(verbose_name='Preferable date for delivery',
                                  default=timezone.now)

    def __str__(self):
        return str(self.id)
