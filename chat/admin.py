from django.contrib import admin

from core.models import User
from .models import ChatRoom, Message, ChatParticipant



# Inline admin for ChatParticipant
class ChatParticipantInline(admin.TabularInline):
    model = ChatParticipant
    extra = 1  # Adds one extra empty form for adding a participant
    fields = ('user', 'is_active')
    readonly_fields = ('user',)



# Registering the ChatRoom model with the @admin.register decorator
@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_group', 'participant_count', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('is_group', 'created_at')
    inlines = [ChatParticipantInline]  # Add participants inline

    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participant Count'



# Registering the Message model with the @admin.register decorator
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('chat_room', 'sender', 'content_snippet', 'timestamp')
    search_fields = ('content', 'sender__username', 'chat_room__name')
    list_filter = ('chat_room', 'sender', 'timestamp')

    def content_snippet(self, obj):
        return obj.content[:50]  # Show a snippet of the message content
    content_snippet.short_description = 'Message Snippet'



# Registering the ChatParticipant model with the @admin.register decorator
@admin.register(ChatParticipant)
class ChatParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'chat_room', 'joined_at', 'is_active')
    search_fields = ('user__username', 'chat_room__name')
    list_filter = ('is_active', 'chat_room', 'joined_at')

    # Adding inline editing of ChatParticipant within the ChatRoomAdmin
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'chat_room')  # Improve query efficiency
