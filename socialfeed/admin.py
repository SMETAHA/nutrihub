from django.contrib import admin
from .models import Post, Reaction, Friendship, Notification

admin.site.register(Post)
admin.site.register(Reaction)
admin.site.register(Friendship)
admin.site.register(Notification)
