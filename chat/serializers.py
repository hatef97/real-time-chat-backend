from rest_framework import serializers

from core.models import User
from .models import ChatRoom, Message, ChatParticipant



# Serializer for ChatRoom model
class ChatRoomSerializer(serializers.ModelSerializer):
    participants = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), many=True)
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'is_group', 'participants', 'created_at', 'updated_at', 'participant_count']

    def get_participant_count(self, obj):
        return obj.participants.count()



# Serializer for Message model
class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.SlugRelatedField(slug_field='username', read_only=True)
    chat_room = serializers.PrimaryKeyRelatedField(queryset=ChatRoom.objects.all(), required=False)

    class Meta:
        model = Message
        fields = ['id', 'chat_room', 'sender', 'content', 'timestamp']
        read_only_fields = ['id', 'sender', 'timestamp']

    def create(self, validated_data):
        request = self.context.get("request")
        if "chat_room" not in validated_data and request is not None:
            room_id = self.context["view"].kwargs.get("room_id") or request.query_params.get("room")
            if room_id:
                validated_data["chat_room"] = ChatRoom.objects.get(pk=room_id)
        return super().create(validated_data)    



# Serializer for ChatParticipant model
class ChatParticipantSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    chat_room = serializers.SlugRelatedField(slug_field='name', queryset=ChatRoom.objects.all())
    
    class Meta:
        model = ChatParticipant
        fields = ['id', 'user', 'chat_room', 'joined_at', 'is_active']
        read_only_fields = ['joined_at']

    def validate_is_active(self, value):
        user = self.instance.user
        chat_room = self.instance.chat_room
        
        # Prevent deactivating the creator (owner) of the chat room
        if not value and chat_room.participants.first() == user:
            raise serializers.ValidationError("The creator of the chat room cannot be deactivated.")
        
        return value
