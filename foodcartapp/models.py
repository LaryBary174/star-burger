from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import F, Sum

class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"

class OrderQuerySet(models.QuerySet):
    def total_sum(self):
        return self.annotate(
            total_sum=Sum(F('orders__quantity') * F('orders__price'))
        )
ORDER_STATUS = (
    ('unprocessed', 'необработанный'),
    ('on kitchen', 'на кухне'),
    ('on the way', 'в пути'),
    ('delivered', 'доставлен')
)
PAYMENT_METHOD = (
    ('unspecified', 'не указан'),
    ('cash', 'наличные'),
    ('money transfer', 'денежный перевод'),
    ('cards', 'картой')
)
class Order(models.Model):
    firstname = models.CharField(
        'Имя',
        max_length=150
    )
    lastname = models.CharField(
        'Фамилия',
        max_length=150
    )
    phonenumber = PhoneNumberField(
        region='RU',
        verbose_name='номер телефона'
    )
    address = models.CharField('адрес',max_length=150)
    status = models.CharField(
        'статус заказа',
        max_length=50,
        choices=ORDER_STATUS,
        default='unprocessed',
        db_index=True,
    )
    comments = models.TextField(
        'комментарии',
        blank=True,
    )
    registrated_at = models.DateTimeField(
        'Дата создания заказа',
        default=timezone.now,
        db_index=True,
    )
    called_at = models.DateTimeField(
        'Дата звонка',
        db_index=True,
        blank=True,
        null=True,
    )
    delivered_at = models.DateTimeField(
        'Дата доставки',
        db_index=True,
        blank=True,
        null=True,
    )
    payment = models.CharField(
        'способ оплаты',
        max_length=50,
        choices=PAYMENT_METHOD,
        default='unspecified',
        db_index=True,
    )
    objects = OrderQuerySet.as_manager()
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f"Заказ {self.id} на имя {self.firstname} по адресу {self.address}"

class OrderItem(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='order_products',
        verbose_name='Продукт'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Заказ'
    )
    quantity = models.PositiveIntegerField(
        verbose_name='Количество'
    )

    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='стоимость'
    )


    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def __str__(self):
        return f'{self.order} - {self.product}'
