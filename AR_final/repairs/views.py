from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import RepairRequest, Appointment
from .forms import RepairRequestForm, AppointmentForm, GarageNoteForm
from garages.models import Garage


# ─── CLIENT : soumettre une demande ─────────────────────────────────────────

@login_required
def request_create(request, garage_id):
    """Le client soumet une demande de réparation à un garage."""
    if request.user.role != 'client':
        return HttpResponseForbidden("Réservé aux clients.")

    garage = get_object_or_404(Garage, pk=garage_id)

    if request.method == 'POST':
        form = RepairRequestForm(request.POST)
        if form.is_valid():
            repair = form.save(commit=False)
            repair.owner = request.user
            repair.garage = garage
            repair.save()
            messages.success(request, "Votre demande a bien été envoyée au garage !")
            return redirect('repairs:client_requests')
    else:
        form = RepairRequestForm()

    return render(request, 'repairs/request_form.html', {
        'form': form,
        'garage': garage,
    })


@login_required
def client_requests(request):
    """Liste des demandes du client connecté."""
    if request.user.role != 'client':
        return HttpResponseForbidden()

    requests_qs = RepairRequest.objects.filter(
        owner=request.user
    ).select_related('garage').prefetch_related('appointment')

    return render(request, 'repairs/client_requests.html', {
        'repair_requests': requests_qs,
    })


@login_required
def request_detail_client(request, pk):
    """Détail d'une demande (vue client)."""
    repair = get_object_or_404(RepairRequest, pk=pk, owner=request.user)
    return render(request, 'repairs/request_detail_client.html', {'repair': repair})


@login_required
def request_cancel_client(request, pk):
    """Le client annule sa demande."""
    repair = get_object_or_404(RepairRequest, pk=pk, owner=request.user)
    if repair.status in (RepairRequest.STATUS_PENDING, RepairRequest.STATUS_ACCEPTED):
        repair.status = RepairRequest.STATUS_CANCELLED
        repair.save()
        messages.success(request, "Votre demande a été annulée.")
    else:
        messages.error(request, "Cette demande ne peut plus être annulée.")
    return redirect('repairs:client_requests')


# ─── GARAGE : gérer les demandes reçues ─────────────────────────────────────

@login_required
def garage_requests(request):
    """Liste des demandes reçues par le garage connecté."""
    if request.user.role != 'garage':
        return HttpResponseForbidden()

    garage = get_object_or_404(Garage, user=request.user)
    requests_qs = RepairRequest.objects.filter(
        garage=garage
    ).select_related('owner').prefetch_related('appointment')

    return render(request, 'repairs/garage_requests.html', {
        'repair_requests': requests_qs,
        'garage': garage,
    })


@login_required
def request_detail_garage(request, pk):
    """Détail d'une demande (vue garage) avec actions."""
    garage = get_object_or_404(Garage, user=request.user)
    repair = get_object_or_404(RepairRequest, pk=pk, garage=garage)

    appt_form = AppointmentForm()
    note_form = GarageNoteForm(instance=repair)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'accept':
            appt_form = AppointmentForm(request.POST)
            if appt_form.is_valid():
                repair.status = RepairRequest.STATUS_ACCEPTED
                repair.save()
                appt = appt_form.save(commit=False)
                appt.repair_request = repair
                appt.status = Appointment.STATUS_CONFIRMED
                appt.save()
                messages.success(request, "Demande acceptée et rendez-vous créé !")
                return redirect('repairs:garage_requests')

        elif action == 'decline':
            note_form = GarageNoteForm(request.POST, instance=repair)
            if note_form.is_valid():
                repair.status = RepairRequest.STATUS_CANCELLED
                note_form.save()
                messages.info(request, "Demande refusée.")
                return redirect('repairs:garage_requests')

        elif action == 'start':
            repair.status = RepairRequest.STATUS_IN_PROGRESS
            repair.save()
            messages.success(request, "Réparation marquée comme en cours.")
            return redirect('repairs:garage_requests')

        elif action == 'done':
            repair.status = RepairRequest.STATUS_DONE
            repair.save()
            messages.success(request, "Réparation marquée comme terminée !")
            return redirect('repairs:garage_requests')

    return render(request, 'repairs/request_detail_garage.html', {
        'repair': repair,
        'appt_form': appt_form,
        'note_form': note_form,
    })
