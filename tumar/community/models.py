import logging

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from ..celery import app
from ..users.utils import compress
from .exceptions import ExceededLinksCountError
from .managers import PostLinkManager

logger = logging.getLogger()

# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=80, verbose_name=_("Name of the Category"))

    class Meta:
        verbose_name = _("Post Category")
        verbose_name_plural = _("Post Categories")

    def __str__(self):
        return self.name


class Post(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name=_("Author"),
    )
    categories = models.ManyToManyField(
        Category, related_name="posts", verbose_name=_("Categories of the Post"),
    )
    title = models.CharField(max_length=100, verbose_name=_("Title of the Post"))
    content = models.TextField(verbose_name=_("Content of the Post"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # TODO VideoField optional

    @property
    def comments_count(self):
        return self.comments.count()

    @property
    def votes_count(self):
        return (
            self.votes.filter(type="U").count(),
            self.votes.filter(type="D").count(),
        )

    class Meta:
        verbose_name = _("Post")
        verbose_name_plural = _("Posts")

    def __str__(self):
        return str(self.pk) + ": " + self.title


class PostImage(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="images", verbose_name=_("Post"),
    )
    image = models.ImageField(upload_to="postimages", max_length=150)

    class Meta:
        verbose_name = _("Post Image")
        verbose_name_plural = _("Post Images")

    def save(self, *args, **kwargs):
        if self.image:
            # call the compress function
            new_image = compress(self.image)

            # set self.image to new_image
            self.image = new_image

        super().save(*args, **kwargs)


class PostLink(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="links", verbose_name=_("Post"),
    )
    type = models.CharField(
        max_length=1,
        choices=[("Y", "YouTube"), ("G", _("General"))],
        default="G",
        verbose_name=_("Type of the Post Link"),
    )
    display_text = models.TextField(blank=True, verbose_name=_("Display Text"))
    url = models.URLField(max_length=300, verbose_name=_("URL Link"))

    objects = PostLinkManager()

    class Meta:
        verbose_name = _("Post Link")
        verbose_name_plural = _("Post Links")

    def save(self, *args, **kwargs):
        if (self.post.links.youtube_links_count() == 1 and self.type == "Y") or (
            self.post.links.general_links_count() == 1 and self.type == "G"
        ):
            raise ExceededLinksCountError(post_pk=self.post.pk)

        super().save(*args, **kwargs)


class PostVote(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="votes", verbose_name=_("Post")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_votes",
        verbose_name=_("User"),
    )
    type = models.CharField(
        max_length=1,
        choices=[("U", _("Upvote")), ("D", _("Downvote"))],
        default="U",
        verbose_name=_("Type of the Vote"),
    )

    class Meta:
        unique_together = ("post", "user")
        verbose_name = _("Upvote/Downvote")
        verbose_name_plural = _("Upvotes/Downvotes")

    def send_push_notification(self):
        if settings.DEBUG:
            logger.info("Notification has been sent!")
        else:
            ntfcn_task = app.signature(
                "send_push_notification.new_vote_on_post",
                kwargs={"post_vote_pk": self.pk},
                queue="community_push_notifications",
                priority=5,
            )

            ntfcn_task.delay()


class Comment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="comments",
        verbose_name=_("User"),
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments", verbose_name=_("Post"),
    )
    reply_object = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name=_("Object of the Reply"),
    )
    content = models.TextField(verbose_name=_("Content of the Comment"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # TODO VideoField optional

    @property
    def votes_count(self):
        return (
            self.votes.filter(type="U").count(),
            self.votes.filter(type="D").count(),
        )

    class Meta:
        verbose_name = _("Comment")
        verbose_name_plural = _("Comments")

    def __str__(self):
        return str(self.pk) + " of " + str(self.post)

    def send_push_notification(self):
        if settings.DEBUG:
            logger.info("Notification has been sent!")
        else:
            ntfcn_task = app.signature(
                "send_push_notification.new_comment_on_post",
                kwargs={"comment_pk": self.pk},
                queue="community_push_notifications",
                priority=5,
            )

            ntfcn_task.delay()

    def send_push_notification_to_reply_object(self):
        if settings.DEBUG:
            logger.info("Notification has been sent!")
        else:
            ntfcn_task = app.signature(
                "send_push_notification.new_reply_comment",
                kwargs={"comment_pk": self.pk},
                queue="community_push_notifications",
                priority=5,
            )

            ntfcn_task.delay()

    def delete(self, *args, **kwargs):

        if self.replies.all().exists():
            self.user = None
            self.content = "[удален]"
            self.save()
        else:
            super().delete(*args, **kwargs)  # Call the "real" delete() method.


class CommentImage(models.Model):
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("Comment"),
    )
    image = models.ImageField(upload_to="commentimages", max_length=150)

    class Meta:
        verbose_name = _("Comment Image")
        verbose_name_plural = _("Comment Images")

    def save(self, *args, **kwargs):
        if self.image:
            # call the compress function
            new_image = compress(self.image)

            # set self.image to new_image
            self.image = new_image

        super().save(*args, **kwargs)


class CommentVote(models.Model):
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name=_("Comment"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comment_votes",
        verbose_name=_("User"),
    )
    type = models.CharField(
        max_length=1,
        choices=[("U", _("Upvote")), ("D", _("Downvote"))],
        default="U",
        verbose_name=_("Type of the Vote"),
    )

    class Meta:
        unique_together = ("comment", "user")
        verbose_name = _("Upvote/Downvote")
        verbose_name_plural = _("Upvotes/Downvotes")

    def send_push_notification(self):
        if settings.DEBUG:
            logger.info("Notification has been sent!")
        else:
            ntfcn_task = app.signature(
                "send_push_notification.new_vote_on_comment",
                kwargs={"comment_vote_pk": self.pk},
                queue="community_push_notifications",
                priority=5,
            )

            ntfcn_task.delay()
