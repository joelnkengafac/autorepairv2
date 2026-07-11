from django import forms
from .models import Payment


class PaymentInitForm(forms.Form):
    """Formulaire de démarrage du paiement Mobile Money."""

    method = forms.ChoiceField(
        label='Moyen de paiement',
        choices=Payment.METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
    )
    phone_number = forms.CharField(
        label='Numéro Mobile Money',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex : 6XXXXXXXX',
        }),
        help_text="Numéro utilisé pour effectuer le paiement (Orange ou MTN)."
    )

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number'].strip().replace(' ', '')
        if not phone.isdigit():
            raise forms.ValidationError("Le numéro ne doit contenir que des chiffres.")
        if len(phone) not in (9, 12):
            raise forms.ValidationError("Numéro invalide (9 ou 12 chiffres attendus).")
        return phone


class PaymentConfirmForm(forms.ModelForm):
    """Formulaire admin : confirmer ou rejeter un paiement."""

    class Meta:
        model = Payment
        fields = ['operator_ref', 'notes']
        widgets = {
            'operator_ref': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Référence reçue de l\'opérateur (Orange/MTN)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Remarques éventuelles...'
            }),
        }
        labels = {
            'operator_ref': 'Référence opérateur',
            'notes':        'Notes',
        }
