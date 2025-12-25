from django.contrib import admin
from .models import *


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'phone', 'total_seats', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'address', 'phone']
    list_editable = ['is_active']
    readonly_fields = ['created_at']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'phone', 'faculty', 'library_card', 'created_at']
    list_filter = ['user_type', 'faculty', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone', 'faculty']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ReadingRoom)
class ReadingRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'branch', 'total_seats', 'available_seats', 'has_computers', 'is_active']
    list_filter = ['branch', 'has_computers', 'has_outlets', 'is_active', 'created_at']
    search_fields = ['name', 'branch__name', 'description']
    readonly_fields = ['created_at']
    list_editable = ['is_active', 'available_seats']

    fieldsets = (
        ('Основная информация', {
            'fields': ('branch', 'name', 'description')
        }),
        ('Вместимость', {
            'fields': ('total_seats', 'available_seats')
        }),
        ('Оснащение', {
            'fields': ('has_computers', 'has_outlets')
        }),
        ('Расписание', {
            'fields': ('opening_hours',)
        }),
        ('Статус', {
            'fields': ('is_active', 'created_at')
        })
    )


@admin.register(RoomBooking)
class RoomBookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'room', 'booking_date', 'start_time', 'end_time', 'seats_count', 'status', 'created_at']
    list_filter = ['status', 'booking_date', 'room__branch', 'created_at']
    search_fields = ['user__username', 'room__name', 'room__branch__name']
    list_editable = ['status', 'seats_count']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'booking_date'

    fieldsets = (
        ('Информация о бронировании', {
            'fields': ('user', 'room', 'status')
        }),
        ('Время и дата', {
            'fields': ('booking_date', 'start_time', 'end_time')
        }),
        ('Количество мест', {
            'fields': ('seats_count',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at')
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'room', 'room__branch')


# Остальные модели остаются без изменений
@admin.register(LibrarianAssignment)
class LibrarianAssignmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'branch', 'can_manage_books', 'can_manage_users', 'can_manage_bookings', 'created_at']
    list_filter = ['can_manage_books', 'can_manage_users', 'can_manage_bookings', 'branch']
    search_fields = ['user__username', 'branch__name']

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'birth_year', 'country', 'created_at']
    list_filter = ['country', 'created_at']
    search_fields = ['full_name', 'country']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'created_at']
    list_filter = ['parent', 'created_at']
    search_fields = ['name', 'description']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'isbn', 'publication_year', 'language', 'created_at']
    list_filter = ['language', 'publication_year']
    search_fields = ['title', 'isbn', 'description']


@admin.register(BookAuthor)
class BookAuthorAdmin(admin.ModelAdmin):
    list_display = ['book', 'author', 'created_at']
    list_filter = ['created_at']
    search_fields = ['book__title', 'author__full_name']
    autocomplete_fields = ['book', 'author']


@admin.register(BookCategory)
class BookCategoryAdmin(admin.ModelAdmin):
    list_display = ['book', 'category', 'created_at']
    list_filter = ['created_at']
    search_fields = ['book__title', 'category__name']
    autocomplete_fields = ['book', 'category']


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    list_display = ['book', 'branch', 'book_count', 'status', 'condition', 'created_at']
    list_filter = ['status', 'condition', 'branch']
    search_fields = ['book__title', 'branch__name']
    list_editable = ['status', 'condition']


@admin.register(BookBooking)
class BookBookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'book_copy', 'branch', 'status', 'created_at', 'ready_by']
    list_filter = ['status', 'branch']
    search_fields = ['user__username', 'book_copy__book__title']
    list_editable = ['status']


@admin.register(BookLoan)
class BookLoanAdmin(admin.ModelAdmin):
    list_display = ['user', 'book_copy', 'issue_date', 'due_date', 'return_date']
    list_filter = [ 'issue_date', 'due_date']
    search_fields = ['user__username', 'book_copy__book__title']


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'reason', 'status', 'created_at', 'paid_at']
    list_filter = ['status', 'reason']
    search_fields = ['user__username', 'reason']
    list_editable = ['status']


@admin.register(BookReview)
class BookReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'rating', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved']
    search_fields = ['user__username', 'book__title']
    list_editable = ['is_approved']


@admin.register(BookQueue)
class BookQueueAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'branch', 'position', 'status', 'created_at']
    list_filter = ['status', 'branch']
    search_fields = ['user__username', 'book__title']
    list_editable = ['status', 'position']


# Настройки админ-панели
admin.site.site_header = "📚 Библиотека КФУ - Панель управления"
admin.site.site_title = "Библиотека КФУ"
admin.site.index_title = "📊 Обзор системы"