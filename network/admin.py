from django.contrib import admin
from .models import User, Post

# Register your models here. Models registered here are for the site admin to have access to
admin.site.register(User)
admin.site.register(Post)
