from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q, Max
from .models import Message
from .forms import MessageForm

User = get_user_model()


@login_required
def inbox(request):
    """
    Liste des conversations de l'utilisateur connecté.
    On regroupe par interlocuteur et on affiche le dernier message.
    """
    me = request.user

    # Tous les utilisateurs avec qui on a échangé
    sent_to     = Message.objects.filter(sender=me).values_list('receiver', flat=True)
    received_from = Message.objects.filter(receiver=me).values_list('sender', flat=True)
    interlocutor_ids = set(list(sent_to) + list(received_from))

    conversations = []
    for uid in interlocutor_ids:
        other = User.objects.get(pk=uid)
        last_msg = Message.objects.filter(
            Q(sender=me, receiver=other) | Q(sender=other, receiver=me)
        ).order_by('-created_at').first()
        unread = Message.objects.filter(sender=other, receiver=me, is_read=False).count()
        conversations.append({
            'user': other,
            'last_message': last_msg,
            'unread': unread,
        })

    # Trier par date du dernier message
    conversations.sort(key=lambda x: x['last_message'].created_at, reverse=True)

    return render(request, 'messaging/inbox.html', {
        'conversations': conversations,
    })


@login_required
def conversation(request, user_id):
    """Affiche et envoie des messages avec un interlocuteur donné."""
    me = request.user
    other = get_object_or_404(User, pk=user_id)

    if me == other:
        return redirect('messaging:inbox')

    # Marquer les messages reçus comme lus
    Message.objects.filter(sender=other, receiver=me, is_read=False).update(is_read=True)

    messages_qs = Message.objects.filter(
        Q(sender=me, receiver=other) | Q(sender=other, receiver=me)
    ).order_by('created_at')

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = me
            msg.receiver = other
            msg.save()
            return redirect('messaging:conversation', user_id=other.pk)
    else:
        form = MessageForm()

    return render(request, 'messaging/conversation.html', {
        'other': other,
        'messages': messages_qs,
        'form': form,
    })


@login_required
def unread_count(request):
    """Retourne le nombre de messages non lus (utilisé dans les templates)."""
    count = Message.objects.filter(receiver=request.user, is_read=False).count()
    return {'unread_messages': count}
