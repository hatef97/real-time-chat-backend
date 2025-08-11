from typing import Any, Dict, Optional

from django.conf import settings
from django.core.validators import URLValidator
from django.utils.text import slugify

from rest_framework import serializers

from .models import User, Profile



class ProfileSerializer(serializers.ModelSerializer):
    # Absolute URL for avatar (useful for frontends)
    avatar_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = ("display_name", "bio", "avatar", "avatar_url")

    def get_avatar_url(self, obj: Profile) -> Optional[str]:
        if not obj.avatar:
            return None
        request = self.context.get("request")
        # If avatar is already absolute, just return it
        if obj.avatar.startswith("http://") or obj.avatar.startswith("https://"):
            return obj.avatar
        # Otherwise, build absolute URL (handles reverse proxies correctly if DRF is set up)
        return request.build_absolute_uri(obj.avatar) if request else obj.avatar

    def validate_display_name(self, value: str) -> str:
        return value.strip()

    def validate_avatar(self, value: str) -> str:
        if not value:
            return value
        URLValidator()(value)  # raises if invalid
        return value



class UserMeSerializer(serializers.ModelSerializer):
    """
    Serializer for /me endpoint.
    - Read: returns user + profile
    - Write (PATCH): allows updating first_name, last_name, and nested profile fields
    """
    profile = ProfileSerializer()
    full_name = serializers.SerializerMethodField(read_only=True)
    effective_display_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        # Keep user surface minimal but useful for most UIs
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "effective_display_name",
            "profile",
        )
        read_only_fields = ("id", "username", "email", "full_name", "effective_display_name")

    # ---------- Read helpers ----------
    def get_full_name(self, obj: User) -> str:
        name = (obj.first_name or "").strip() + " " + (obj.last_name or "").strip()
        return name.strip() or obj.get_username()

    def get_effective_display_name(self, obj: User) -> str:
        # Prefer profile.display_name, then full_name, then username
        prof = getattr(obj, "profile", None)
        if prof and prof.display_name:
            return prof.display_name.strip()
        return self.get_full_name(obj) or obj.get_username()

    # ---------- Write (nested update) ----------
    def update(self, instance: User, validated_data: Dict[str, Any]) -> User:
        """
        Allow PATCH to update first_name, last_name, and nested profile fields.
        We keep this intentionally narrow to avoid accidentally exposing privileged fields.
        """
        profile_data = validated_data.pop("profile", None)

        # Update basic user fields
        for field in ("first_name", "last_name"):
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save(update_fields=["first_name", "last_name"])

        # Ensure a profile exists (signals should create it, but be defensive)
        profile: Profile = getattr(instance, "profile", None)
        if profile is None:
            profile = Profile.objects.create(user=instance)

        # Update allowed profile fields
        if profile_data:
            changed = False
            for field in ("display_name", "bio", "avatar"):
                if field in profile_data:
                    setattr(profile, field, profile_data[field])
                    changed = True
            if changed:
                profile.save()

        return instance
