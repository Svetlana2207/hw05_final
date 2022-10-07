from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import page_quan


@cache_page(20)
def index(request):
    template = 'posts/index.html'
    posts = Post.objects.select_related('group', 'author').all()
    page_obj = page_quan(posts, request)
    index = True
    context = {
        'page_obj': page_obj['page_object'],
        'index': index,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = page_quan(posts, request)
    context = {
        'group': group,
        'page_obj': page_obj['page_object'],
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page_obj = page_quan(posts, request)
    post_count = posts.count()
    following = False

    if request.user.is_authenticated:
        following = author.following.filter(user=request.user).exists()
    sub = (author != request.user)
    context = {
        'page_obj': page_obj['page_object'],
        'author': author,
        'post_count': post_count,
        'following': following,
        'sub': sub,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    post_count = post.author.posts.count()
    form = CommentForm(request.POST)
    comments = post.comments.all()
    context = {
        'post': post,
        'post_count': post_count,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create.html'
    form = PostForm(request.POST or None, files=request.FILES or None)
    context = {
        'form': form,
    }
    if request.method == 'POST':
        if form.is_valid():
            form = form.save(commit=False)
            form.author = request.user
            form.save()
            return redirect('posts:profile', form.author.username)
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create.html'
    post = get_object_or_404(Post, pk=post_id)
    is_edit = True
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'is_edit': is_edit,
        'post': post,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = page_quan(posts, request)
    follow = True
    context = {
        'page_obj': page_obj['page_object'],
        'follow': follow,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect('posts:profile', username=username)
    get_object_or_404(Follow, user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
