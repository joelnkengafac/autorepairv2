from django import forms
from .models import RepairRequest, Appointment


class RepairRequestForm(forms.ModelForm):
    class Meta:
        model = RepairRequest
        fields = ['type_service', 'vehicle_description', 'description']
        widgets = {
            'type_service': forms.Select(attrs={'class': 'form-select'}),
            'vehicle_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex : Toyota Corolla 2015, immatriculation LT 123 A'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Décrivez le problème de votre véhicule en détail...'
            }),
        }
        labels = {
            'type_service': 'Type de service',
            'vehicle_description': 'Votre véhicule',
            'description': 'Description du problème',
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['scheduled_at', 'notes']
        widgets = {
            'scheduled_at': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Informations complémentaires pour le rendez-vous...'
            }),
        }
        labels = {
            'scheduled_at': 'Date et heure du rendez-vous',
            'notes': 'Notes (optionnel)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['scheduled_at'].input_formats = ['%Y-%m-%dT%H:%M']


class GarageNoteForm(forms.ModelForm):
    """Formulaire pour que le garage laisse une note/réponse sur la demande."""
    class Meta:
        model = RepairRequest
        fields = ['garage_note']
        widgets = {
            'garage_note': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Message à envoyer au propriétaire...'
            }),
        }
        labels = {'garage_note': 'Message au client'}
