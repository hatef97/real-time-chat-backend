from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import User, Profile



class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"
    fields = ("display_name", "bio", "avatar", "avatar_preview")

    readonly_fields = ("avatar_preview",)

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" style="max-height:80px; border-radius:6px;"/>', obj.avatar)
        return "—"
    avatar_preview.short_description = "Avatar Preview"



@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ("id", "avatar_thumb", "username", "email", "is_active", "is_staff", "date_joined")
    list_filter = ("is_active", "is_staff", "date_joined")
    search_fields = ("username", "email", "profile__display_name", "profile__bio")
    ordering = ("-date_joined",)

    def avatar_thumb(self, obj):
        if hasattr(obj, "profile") and obj.profile.avatar:
            return format_html('<img src="{}" style="height:40px; border-radius:50%;"/>', obj.profile.avatar)
        return "—"
    avatar_thumb.short_description = "Avatar"



@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "display_name", "avatar_preview", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "display_name", "bio")
    readonly_fields = ("created_at", "updated_at", "avatar_preview")

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" style="max-height:80px; border-radius:6px;"/>', obj.avatar)
        return "—"
    avatar_preview.short_description = "Avatar"
