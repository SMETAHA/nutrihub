from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Post, Reaction, Friendship, Notification
from .forms import PostForm

@login_required
def feed(request):
    friends = Friendship.objects.filter(user=request.user).values_list('friend_id', flat=True)
    qs = Post.objects.filter(user__in=list(friends)+[request.user.id]).order_by('-created_at')[:100]
    form = PostForm()
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            p.user = request.user
            p.save()
            return redirect('feed')
    return render(request, 'social/feed.html', {'posts': qs, 'form': form})

@login_required
def add_friend(request, username):
    target = get_object_or_404(User, username=username)
    if target != request.user:
        Friendship.objects.get_or_create(user=request.user, friend=target)
    return redirect('profile', username=target.username)

@login_required
def react(request, post_id, kind='like'):
    post = get_object_or_404(Post, pk=post_id)
    Reaction.objects.get_or_create(user=request.user, post=post, kind=kind)
    if post.user != request.user:
        Notification.objects.create(user=post.user, message=f'{request.user.username} реагировал(а) на ваш пост')
    return redirect('feed')
