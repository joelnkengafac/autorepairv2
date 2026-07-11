from django.db import models
from django.conf import settings


class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Expéditeur'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages',
        verbose_name='Destinataire'
    )
    content = models.TextField('Message')
    is_read = models.BooleanField('Lu', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username} ({self.created_at.strftime('%d/%m/%Y %H:%M')})"
