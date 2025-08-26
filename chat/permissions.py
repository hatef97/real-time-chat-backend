from rest_framework.permissions import BasePermission



class IsRoomParticipant(BasePermission):
    message = "You must be a participant of this chat room."

    def has_object_permission(self, request, view, obj):
        # obj can be ChatRoom, Message, ChatParticipant
        if hasattr(obj, "participants"):          
            room = obj
        elif hasattr(obj, "chat_room"):           
            room = obj.chat_room
        else:
            return False
        return room.participants.filter(id=request.user.id).exists()
