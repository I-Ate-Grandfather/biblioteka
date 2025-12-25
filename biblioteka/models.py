from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class Branch(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название филиала")
    address = models.TextField(verbose_name="Адрес")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    email = models.EmailField(blank=True, verbose_name="Email")
    opening_hours = models.JSONField(default=dict, verbose_name="Часы работы")
    total_seats = models.IntegerField(default=0, verbose_name="Всего мест")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Филиал библиотеки"
        verbose_name_plural = "Филиалы библиотек"

    def __str__(self):
        return self.name


class Profile(models.Model):
    USER_TYPES = (
        ('guest', 'Гость'),
        ('reader', 'Читатель'),
        ('librarian', 'Библиотекарь'),
        ('admin', 'Администратор'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='guest', verbose_name="Тип пользователя")  # Изменен default на 'guest'
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    faculty = models.CharField(max_length=100, blank=True, verbose_name="Факультет")
    student_group = models.CharField(max_length=50, blank=True, verbose_name="Группа")
    library_card = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Читательский билет")  # Изменено: может быть пустым для гостей
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_user_type_display()})"

    def save(self, *args, **kwargs):
        # Для гостей библиотечный билет не требуется
        if self.user_type == 'guest' and self.library_card:
            self.library_card = None
        super().save(*args, **kwargs)


class LibrarianAssignment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Библиотекарь")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="Филиал")
    can_manage_books = models.BooleanField(default=False, verbose_name="Может управлять книгами")
    can_manage_users = models.BooleanField(default=False, verbose_name="Может управлять пользователями")
    can_manage_bookings = models.BooleanField(default=False, verbose_name="Может управлять бронированиями")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Назначение библиотекаря"
        verbose_name_plural = "Назначения библиотекарей"
        unique_together = ['user', 'branch']

    def __str__(self):
        return f"{self.user.username} - {self.branch.name}"


class Author(models.Model):
    full_name = models.CharField(max_length=200, verbose_name="Полное имя")
    birth_year = models.IntegerField(null=True, blank=True, verbose_name="Год рождения")
    country = models.CharField(max_length=100, blank=True, verbose_name="Страна")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Автор"
        verbose_name_plural = "Авторы"

    def __str__(self):
        return self.full_name


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Родительская категория")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class Book(models.Model):
    isbn = models.CharField(max_length=20, unique=True, blank=True, verbose_name="ISBN")
    title = models.CharField(max_length=500, verbose_name="Название")
    publication_year = models.IntegerField(null=True, blank=True, verbose_name="Год издания")
    language = models.CharField(max_length=50, default="Русский", verbose_name="Язык")
    description = models.TextField(blank=True, verbose_name="Описание")
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, verbose_name="Обложка")
    pages = models.IntegerField(null=True, blank=True, verbose_name="Страниц")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=500.00, verbose_name="Стоимость")
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        verbose_name = "Книга"
        verbose_name_plural = "Книги"

    def __str__(self):
        return self.title

    def get_authors_display(self):
        """Возвращает строку с именами авторов"""
        authors = self.bookauthor_set.select_related('author').all()
        if not authors:
            return "Не указан"

        author_names = []
        for book_author in authors:
            name_parts = []
            if book_author.author.full_name:
                name_parts.append(book_author.author.full_name)
            if name_parts:
                author_names.append(" ".join(name_parts))

        return ", ".join(author_names) if author_names else "Не указан"

    def get_available_copies_count(self):
        """Возвращает общее количество доступных экземпляров"""
        copies = self.bookcopy_set.filter(status='active')
        total = 0
        for copy in copies:
            total += copy.book_count
        return total

    def is_available(self):
        """Проверяет, доступна ли книга"""
        return self.get_available_copies_count() > 0

class BookAuthor(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="Книга")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Автор книги"
        verbose_name_plural = "Авторы книг"
        unique_together = ['book', 'author']

    def __str__(self):
        return f"{self.book.title} - {self.author.full_name}"


class BookCategory(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="Книга")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Категория книги"
        verbose_name_plural = "Категории книг"
        unique_together = ['book', 'category']

    def __str__(self):
        return f"{self.book.title} - {self.category.name}"


class BookCopy(models.Model):
    STATUS_CHOICES = (
        ('active', 'Активно'),
        ('returned', 'Возвращена'),
        ('overdue', 'Просрочена'),
        ('lost', 'Утеряна'),
    )

    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="Книга")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="Филиал")
    book_count = models.IntegerField(default=1, verbose_name="Количество книг")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Статус")
    acquisition_date = models.DateField(null=True, blank=True, verbose_name="Дата выдачи")
    return_date = models.DateField(null=True, blank=True, verbose_name="Срок возврата")
    condition = models.CharField(max_length=50, default='good', verbose_name="Состояние")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Экземпляр книги"
        verbose_name_plural = "Экземпляры книг"

    def __str__(self):
        return f"{self.book.title} ({self.book_count})"

    def save(self, *args, **kwargs):
        # Автоматически устанавливаем срок возврата при выдаче книги
        if self.acquisition_date and not self.return_date:
            # Устанавливаем срок возврата через 14 дней от даты выдачи
            self.return_date = self.acquisition_date + timedelta(days=14)

        # Автоматически обновляем статус на "просрочена" если срок возврата прошел
        if self.return_date and self.status == 'active' and self.return_date < timezone.now().date():
            self.status = 'overdue'

        super().save(*args, **kwargs)

    def is_overdue(self):
        """Проверяет, просрочена ли книга"""
        return self.status == 'active' and self.return_date and self.return_date < timezone.now().date()


class BookBooking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Обрабатывается'),
        ('ready', 'Готов к выдаче'),
        ('issued', 'Выдан'),
        ('cancelled', 'Отменен'),
        ('expired', 'Просрочен'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    book_copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE, verbose_name="Экземпляр книги")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="Филиал")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True)
    ready_by = models.DateTimeField(null=True, blank=True, verbose_name="Готов к")
    pickup_deadline = models.DateTimeField(null=True, blank=True, verbose_name="Забрать до")
    class Meta:
        verbose_name = "Бронирование книги"
        verbose_name_plural = "Бронирования книг"

    def __str__(self):
        return f"{self.user.username} - {self.book_copy.book.title}"


class BookLoan(models.Model):
    STATUS_CHOICES = (
        ('active', 'Активно'),
        ('returned', 'Возвращена'),
        ('overdue', 'Просрочена'),
        ('lost', 'Утеряна'),
        ('fine_paid', 'Штраф оплачен'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    book_copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE, verbose_name="Экземпляр книги")
    booking = models.OneToOneField(BookBooking, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="Бронирование")
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='issued_loans',
                                  verbose_name="Кто выдал")
    issue_date = models.DateTimeField(default=timezone.now, verbose_name="Дата выдачи")
    due_date = models.DateTimeField(verbose_name="Вернуть до")
    return_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата возврата")
    returned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='returned_loans', verbose_name="Кто принял")
    renewals = models.IntegerField(default=0, verbose_name="Продления")

    # Добавляем поле статуса
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Статус"
    )

    # Убираем старое поле is_overdone
    # is_overdue = models.BooleanField(default=False, verbose_name="Просрочка")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Выдача книги"
        verbose_name_plural = "Выдачи книг"

    def __str__(self):
        return f"{self.user.username} - {self.book_copy.book.title}"

    def save(self, *args, **kwargs):
        """Автоматически обновляем статус при сохранении"""
        # Если книга возвращена
        if self.return_date and self.status != 'returned':
            self.status = 'returned'

        # Если не возвращена и срок прошел
        elif not self.return_date and timezone.now() > self.due_date and self.status != 'lost' and self.status != 'fine_paid':
            self.status = 'overdue'

        super().save(*args, **kwargs)

    def get_status_display(self):
        """Возвращает читаемое название статуса"""
        return dict(self.STATUS_CHOICES).get(self.status, 'Неизвестно')


class ReadingRoom(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="Филиал")
    name = models.CharField(max_length=100, verbose_name="Название")
    total_seats = models.IntegerField(verbose_name="Всего мест")
    available_seats = models.IntegerField(default=0, verbose_name="Доступно мест")
    has_computers = models.BooleanField(default=False, verbose_name="Есть компьютеры")
    has_outlets = models.BooleanField(default=False, verbose_name="Есть розетки")
    opening_hours = models.JSONField(default=dict, verbose_name="Часы работы")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Читальный зал"
        verbose_name_plural = "Читальные залы"
        unique_together = ['branch', 'name']

    def __str__(self):
        return f"{self.branch.name} - {self.name}"

    def get_occupied_seats(self, date, start_time, end_time):
        from .models import RoomBooking
        bookings = RoomBooking.objects.filter(
            room=self,
            booking_date=date,
            status='confirmed',
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        return sum(booking.seats_count for booking in bookings)

    def is_available(self, date, start_time, end_time, seats_needed=1):
        occupied = self.get_occupied_seats(date, start_time, end_time)
        return self.available_seats - occupied >= seats_needed


class RoomBooking(models.Model):
    STATUS_CHOICES = (
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
        ('completed', 'Завершено'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    room = models.ForeignKey(ReadingRoom, on_delete=models.CASCADE, verbose_name="Зал")
    booking_date = models.DateField(verbose_name="Дата бронирования")
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")
    seats_count = models.IntegerField(default=1, verbose_name="Количество мест")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Бронирование места"
        verbose_name_plural = "Бронирования мест"
        unique_together = ['room', 'booking_date', 'start_time', 'end_time']

    def __str__(self):
        return f"{self.user.username} - {self.room.name} - {self.booking_date}"


class Fine(models.Model):
    STATUS_CHOICES = (
        ('unpaid', 'Не оплачен'),
        ('paid', 'Оплачен'),
        ('cancelled', 'Отменен'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    loan = models.ForeignKey(BookLoan, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Выдача книги")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    reason = models.CharField(max_length=200, verbose_name="Причина")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unpaid', verbose_name="Статус")
    payment_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID платежа в ЮKassa")
    yookassa_payment_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID платежа в ЮKassa")
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата оплаты")

    class Meta:
        verbose_name = "Штраф"
        verbose_name_plural = "Штрафы"

    def __str__(self):
        return f"{self.user.username} - {self.amount} руб."

    def mark_as_paid(self, payment_id=None):
        """Пометить штраф как оплаченный"""
        self.status = 'paid'
        self.paid_at = timezone.now()
        if payment_id:
            self.yookassa_payment_id = payment_id
        self.save()

        # Обновляем статус книги
        if self.loan:
            self.loan.status = 'fine_paid'
            self.loan.save()

class BookReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="Книга")
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Рейтинг"
    )
    review_text = models.TextField(verbose_name="Текст отзыва")
    is_approved = models.BooleanField(default=False, verbose_name="Одобрен")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Отзыв о книге"
        verbose_name_plural = "Отзывы о книгах"
        unique_together = ['user', 'book']

    def __str__(self):
        return f"{self.user.username} - {self.book.title} - {self.rating}★"


class BookQueue(models.Model):
    STATUS_CHOICES = (
        ('waiting', 'В ожидании'),
        ('notified', 'Уведомлен'),
        ('cancelled', 'Отменен'),
        ('completed', 'Завершено'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="Книга")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Филиал")
    position = models.IntegerField(verbose_name="Позиция в очереди")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True)
    notified_at = models.DateTimeField(null=True, blank=True, verbose_name="Время уведомления")

    class Meta:
        verbose_name = "Очередь на книгу"
        verbose_name_plural = "Очереди на книги"
        unique_together = ['user', 'book', 'branch']

    def __str__(self):
        return f"{self.user.username} - {self.book.title} - Позиция {self.position}"