from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "status", "chunk_count", "uploaded_at")
    list_filter = ("status",)
    search_fields = ("title", "file_name")
    readonly_fields = ("uploaded_at",)
