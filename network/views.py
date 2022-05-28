from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import datetime

from .models import User, Post


def index(request):
    """ If this route receives a POST request, it takes the data submitted to create a new form
        Else it loads the default home page with all posts 
    """
    if request.method == "POST":
        """ This route is accessed when a user submits a form to create a new post. """
        # Get data needed to populate the database
        username = request.user.username
        text = request.POST["post_text"]
        time = datetime.datetime.now()
        user = User.objects.get(username=username)

        # Create a post object using the data, and save it to the database
        p = Post(user=user, content=text, created=time)
        p.save()
        posts = Post.objects.all().order_by("-created")
        paginator = Paginator(posts, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        # Reload the index page with all posts
        return render(request, "network/index.html", {
            "page_obj": page_obj
        })

    posts = Post.objects.all().order_by("-created")
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "network/index.html", {
        "page_obj": page_obj 
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")


def profile(request, user):
    """ Given a user 'user', return a profile page of the user's details """
    if request.method == "POST":
        to_follow = User.objects.get(username=user)
        curr_user = User.objects.get(username=request.user)
        action = request.POST["follow"]

        if action == "follow":
            curr_user.following.add(to_follow)
        else:
            curr_user.following.remove(to_follow)

        return HttpResponseRedirect(reverse("index"))


    user = User.objects.get(username=user)
    curr_follows = None
    #print(user, user.followers.all(), user.following.all(), user.posts.all())

    if request.user:
        curr_follows = user.followers.filter(username=request.user).exists()

    followers = user.followers.all().count()
    print(followers)
    following = user.following.count()
    print(following)
    posts = Post.objects.filter(user=user).all().order_by("-created")
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    return render(request, "network/profile.html", {
        "profile": user,
        "followers": followers,
        "following": following,
        "page_obj": page_obj,
        "curr_follows": curr_follows
    })


def following(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))

    following = User.objects.get(username=request.user).following.all()
    posts = Post.objects.filter(user__in=following).all().order_by("-created")
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "network/following.html", {
        "page_obj": page_obj
    })

@csrf_exempt
def edit(request, post_id):
    # Retrieve the post the user wishes to edit from the database
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "post does not exist"}, status=404)
    
    # Retrieve the new content of the post
    data = json.loads(request.body)
    content = data.get("content", "")
    
    # Update the field in the database to reflect the edit made by the user, and send a success message
    post.content = content
    post.save()

    return JsonResponse({"success": "post successfully updated"}, status=200)

@csrf_exempt
def like(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"error": "post does not exist"}, status=404)
    
    user = User.objects.get(username=request.user)
    data = json.loads(request.body)
    action = data.get("action", "")
    
    if action == "like":
        post.likes.add(user)
        post.save()
    elif action == "unlike":
        post.likes.remove(user)
        post.save()
    
    return JsonResponse({"success": "Like/Unlike action completed"}, status=200)
