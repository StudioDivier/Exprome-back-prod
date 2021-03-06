import jwt
from taggit.managers import TaggableManager
from ckeditor.fields import RichTextField

from datetime import datetime
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser,AbstractUser
from django.contrib.auth.models import PermissionsMixin
from django.core import validators
from django.db import models
from django.contrib.auth.models import BaseUserManager
from django.utils import timezone
from django.conf import settings

from django.dispatch import receiver
from django.urls import reverse
from django_rest_passwordreset.signals import reset_password_token_created
from django.core.mail import send_mail
from MyStar import config
import uuid


def nameFile(instance, filename):
    """
    Сохраяем в каталог файл при загрузке
    Аватар пользователей
    :param instance:
    :param filename:
    :return:
    """
    filename = str(uuid.uuid4()) + '.jpeg'
    return '/'.join(['avatars', filename])


def nameCat(instance, filename):
    """
    Сохраяем в каталог файл при загрузке
    Изображение категории
    :param instance:
    :param filename:
    :return:
    """
    filename = str(uuid.uuid4()) + '.svg'
    return '/'.join(['categories', filename])


def nameVideoFile(instance, filename):
    """
    Сохраяем в каталог файл при загрузке
    Видео
    :param instance:
    :param filename:
    :return:
    """
    filename = str(uuid.uuid4()) + '.mp4'
    return '/'.join(['videos', str(instance.username), filename])


def exVideoFile(instance, filename):
    """
    Сохраяем в каталог файл при загрузке
    Видео
    :param instance:
    :param filename:
    :return:
    """
    filename = str(uuid.uuid4()) + '.mp4'
    return '/'.join(['ex-videos', filename])


def congratulationFile(instance, filename):
    """
    Сохраяем в каталог файл при загрузке
    Видео поздравление
    :param instance:
    :param filename:
    :return:
    """
    filename = str(uuid.uuid4()) + '.mp4'
    return '/'.join(['congratulation', str(instance.star_id), filename])


class CatPhoto(models.Model):
    """
    Модель для фото категорий
    """
    category = models.CharField(name='category', unique=True, max_length=128)
    image = models.FileField(upload_to=nameCat)

    def __str__(self):
        return str(self.image)

    class Meta:
        verbose_name = 'Фото категории'
        verbose_name_plural = 'Фото категорий'


class Avatars(models.Model):
    """
    Модель для фото аватарок
    """
    username = models.CharField(name='username', unique=True, max_length=128)
    image = models.ImageField(upload_to=nameFile)

    class Meta:
        verbose_name = 'Аватар'
        verbose_name_plural = 'Аватары'

    def __str__(self):
        return str(self.username)


class Videos(models.Model):
    """
    Модель для видео
    """
    username = models.CharField(name='username', unique=True, max_length=128)
    video_hi = models.FileField(upload_to=nameVideoFile)

    class Meta:
        verbose_name = 'Видео приветствие'
        verbose_name_plural = 'Видео приветствия'

    def __str__(self):
        return str(self.username)


class Congratulations(models.Model):
    """
    Модель для видео поздравление
    """
    star_id = models.IntegerField(name='star_id')
    video_con = models.FileField(upload_to=congratulationFile)
    order_id = models.IntegerField(name='order_id', unique=True)

    class Meta:
        verbose_name = 'congritulation'
        verbose_name_plural = 'congritulations'

    def __str__(self):
        return str(self.video_con)


class UserManager(BaseUserManager):
    """
    Django требует, чтобы пользовательские `User`
    определяли свой собственный класс Manager.
    Унаследовав от BaseUserManager, мы получаем много кода,
    используемого Django для создания `User`.

    Все, что нам нужно сделать, это переопределить функцию
    `create_user`, которую мы будем использовать
    для создания объектов `User`.
    """

    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('Указанное имя пользователя должно быть установлено')

        if not email:
            raise ValueError('Данный адрес электронной почты должен быть установлен')

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user


class Users(AbstractUser, PermissionsMixin):
    """
    Родительский класс для всех пользователей
     username - имя пользователя
     phone - мобильный телефон пользователя
     email - эл.адрес пользователя
     password - пароль пользователя
     avatar - аватар пользователя
     is_star - флаг для чека звезды (0,1)
    """
    username = models.CharField(name='username', max_length=128, db_index=True, unique=True)
    phone = models.BigIntegerField(name='phone', unique=True)
    email = models.EmailField(name='email', unique=True)
    password = models.CharField(name='password', max_length=128)
    avatar = models.ForeignKey(Avatars, on_delete=models.CASCADE, blank=True, null=True)
    #avatar = models.FilePathField(name='avatar', path=settings.AVATAR_ROOT, blank=True)
    # avatar = models.ImageField(
    #     upload_to=nameFile,
    #     max_length=254, blank=True, null=True
    # )
    is_star = models.BooleanField(name='is_star', default=0)

    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    register = models.CharField(name='register', max_length=32, blank=True, default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username',)

    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'BaseUser'
        verbose_name_plural = 'BaseUsers'

    @property
    def token(self):
        """
        Позволяет нам получить токен пользователя, вызвав `user.token` вместо
        `user.generate_jwt_token().

        Декоратор `@property` выше делает это возможным.
        `token` называется «динамическим свойством ».
        """
        return self._generate_jwt_token()

    def _generate_jwt_token(self):
        """
        Создает веб-токен JSON, в котором хранится идентификатор
        этого пользователя и срок его действия
        составляет 60 дней в будущем.
        """
        dt = datetime.now() + timedelta(days=60)

        token = jwt.encode({
            'id': self.pk,
            'exp': dt.utcfromtimestamp(dt.timestamp())
        }, settings.SECRET_KEY, algorithm='HS256')

        return token.decode('utf-8')


class Customers(Users):
    """
    Модель для заказчиков
     date_of_birth - дата рождения заказчика

    """
    date_of_birth = models.DateField(name='date_of_birth', blank=True, null=True)
    confirm = models.BooleanField(name='confirm', default=0)

    class Meta:
        verbose_name = 'Заказчик'
        verbose_name_plural = 'Заказчики'


class Categories(models.Model):
    """
    Модель категорий
     cat_name - наименование категории
    """
    cat_name = models.CharField(name='cat_name', unique=True, db_index=True, max_length=128)
    cat_photo = models.ForeignKey(CatPhoto, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return "{}".format(self.cat_name)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Ratings(models.Model):
    """
    Модель рейтинга
     rate - рейтинг
     adresat - От кого (заказчик)
     adresant - Кому (Звезда)
    """
    rating = models.IntegerField(name='rating')
    adresat = models.ForeignKey(Customers, name='adresat', on_delete=models.CASCADE)
    adresant = models.IntegerField(name='adresant', default=None)

    def __str__(self):
        return "{}".format(self.rating)

    class Meta:
        verbose_name = 'rating'
        verbose_name_plural = 'ratings'


class Stars(Users):
    """
    Модель для Исполнителей (звезд)
     price - цена звезды
     cat_name_id - id Катгории
     rating - отсылка к модели Рейтинга
     video_hi - видео приветствие от звезды
    """
    price = models.DecimalField(name='price', max_digits=9, decimal_places=2, verbose_name='Ценник')
    price_another = models.DecimalField(name='price_another', max_digits=9, decimal_places=2, verbose_name='Ценник еще')
    cat_name_id = models.ForeignKey(Categories, to_field='id', on_delete=models.CASCADE, verbose_name='Категория')
    rating = models.IntegerField(name='rating', verbose_name='Рейтинг')
    days = models.CharField(name='days', default='0', max_length=8, verbose_name='Дней выполнения заказа')
    # video_hi = models.FilePathField(name='video_hi', path=settings.VIDEO_ROOT, default='/videos/012155be-4a77-4fdd-adbc-4121c5dceda0.mp4')
    video_hi = models.ForeignKey(Videos, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Видео-приветсвие')
    profession = models.CharField(name='profession', max_length=32, verbose_name='Проффесия')
    tags = TaggableManager()
    description = models.TextField(name='description', max_length=2048, verbose_name='Описание')
    top = models.BooleanField(name="top", default=False, verbose_name='Топ10')
    sorted = models.IntegerField(name='sorted', verbose_name='Сортировка', blank=True, null=True)

    class Meta:
        verbose_name = 'Звезда'
        verbose_name_plural = 'Звезды'


class Favorites(models.Model):
    star_id = models.IntegerField(name='star_id')
    cust_id = models.IntegerField(name='cust_id')

    class Meta:
        unique_together = ('star_id', 'cust_id')


class Likes(models.Model):
    """
    Модель для лайков
    """
    star_id = models.IntegerField(name='star_id')
    cust_id = models.IntegerField(name='cust_id')
    like = models.BooleanField(name='like', default=1)

    class Meta:
        unique_together = ('star_id', 'cust_id')


class MessageChats(models.Model):
    """
    Модель для сообщений между поьлователями
    """
    chat_id = models.IntegerField(name='chat_id')
    from_user = models.IntegerField(name='from_user')
    message_id = models.IntegerField(name='message_id')
    message = models.CharField(name='message', max_length=256)

    def __str__(self):
        return "message from user {}".format(self.from_user)


class Orders(models.Model):
    """
    Модель для Заказов
      customer_id - id заказчика
      star_id - id звезды
      order_price - цена заказа
      ordering_time - время заказа
      for_whom - для кого
      comment - колмментарий к заказы
      status_order - статус заказа (0 - New, 1 - Accepted, 2 - Completed)
    """

    customer_id = models.ForeignKey(Customers, name='customer_id', on_delete=models.CASCADE)
    star_id = models.ForeignKey(Stars, name='star_id', on_delete=models.CASCADE)
    payment_id = models.CharField(name='payment_id', max_length=128, default='', blank=True)
    order_price = models.DecimalField(name='order_price', max_digits=9, decimal_places=2)
    ordering_time = models.DateTimeField(name='ordering_time', default=timezone.now)
    by_date = models.DateField(name='by_date', default=None)
    by_time = models.TimeField(name='by_time', default=datetime.today().strftime('%H:%M'))
    for_whom = models.CharField(name='for_whom', max_length=128)
    comment = models.TextField(name='comment')
    status_order = models.IntegerField(name='status_order', default=0)
    type = models.CharField(name='type', max_length=128, blank=True, null=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return "Заказ №{}: {} -> {}".format(self.id, self.customer_id, self.star_id)


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):

    email_plaintext_message = "https://exprome.ru{}confirm/?token={}".format(
        reverse('password_reset:reset-password-request'
                ), reset_password_token.key)

    send_mail(
        # title:
        "Password Reset for {title}".format(title="EXPROME"),
        # message:
        email_plaintext_message,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [reset_password_token.user.email]
    )


class YandexUsers(models.Model):
    """
    Модель для отслеживания пользователей юзеров
    """
    id_yandex = models.BigIntegerField(name='id_yandex', unique=True)
    access_token = models.CharField(name='access_token', max_length=256)
    refresh_token = models.CharField(name='refresh_token', max_length=256)
    expires_in = models.BigIntegerField(name='expires_in')

    def __str__(self):
        return str(self.id_yandex)


class VkUsers(models.Model):
    """
    Модель для отслеживания поьлзователей из вк
    """
    id_vk = models.BigIntegerField(name='id_vk', unique=True)
    access_token = models.CharField(name='access_token', max_length=256)
    expires_in = models.BigIntegerField(name='expires_in')

    def __str__(self):
        return str(self.id_vk)


class RequestsForm(models.Model):
    """
    Модель для формы создания звезды
    """
    name = models.CharField(name='name', max_length=256)
    phone = models.BigIntegerField(name='phone')
    email = models.EmailField(name='email')

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'


class CongratulationPage(models.Model):
    content = models.TextField(name='content', max_length=2048)

    class Meta:
        verbose_name = 'Видео-поздравление(пример)'
        verbose_name_plural = 'Видео поздравления(примеры)'


class CongratulationPageVideos(models.Model):
    page = models.ForeignKey(CongratulationPage, on_delete=models.CASCADE)
    video = models.FileField(upload_to=exVideoFile)
