from django.contrib import admin

from .models import Document, TopicExtractionResult


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "status", "chunk_count", "uploaded_at")
    list_filter = ("status",)
    search_fields = ("title", "file_name")
    readonly_fields = ("uploaded_at",)


@admin.register(TopicExtractionResult)
class TopicExtractionResultAdmin(admin.ModelAdmin):
    list_display = ("document", "model_used", "extracted_at")
    list_filter = ("model_used", "extracted_at")
    search_fields = ("document__title",)
