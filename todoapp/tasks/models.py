# pyrefly: ignore [missing-import]
from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class Todo(models.Model):

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("archived", "Archived"),
    )

    PRIORITY_CHOICES = (
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="todos"
    )

    category = models.ForeignKey(
        "Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    title = models.CharField(max_length=255)

    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="medium"
    )

    due_date = models.DateField(
        null=True,
        blank=True
    )

    reminder = models.DateTimeField(
        null=True,
        blank=True
    )

    is_pinned = models.BooleanField(default=False)

    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "todos"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

class User(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    google_id = models.CharField(max_length=100, unique=True)
    picture = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.email



class Category(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="categories"
    )

    name = models.CharField(max_length=100)

    color = models.CharField(max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "categories"

    def __str__(self):
        return self.name

class Tag(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=50)

    class Meta:
        db_table = "tags"

    def __str__(self):
        return self.name

class TodoTag(models.Model):

    todo = models.ForeignKey(
        Todo,
        on_delete=models.CASCADE
    )

    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = "todo_tags"

class Attachment(models.Model):

    todo = models.ForeignKey(
        Todo,
        on_delete=models.CASCADE,
        related_name="attachments"
    )

    file = models.FileField(
        upload_to="attachments/"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "attachments"

class Comment(models.Model):

    todo = models.ForeignKey(
        Todo,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    comment = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "comments"

class Notification(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    message = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"

class ActivityLog(models.Model):

    ACTIONS = (
        ("created", "Created"),
        ("updated", "Updated"),
        ("deleted", "Deleted"),
        ("completed", "Completed"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    todo = models.ForeignKey(
        Todo,
        on_delete=models.CASCADE
    )

    action = models.CharField(
        max_length=50,
        choices=ACTIONS
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "activity_logs"

