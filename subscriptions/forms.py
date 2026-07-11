from django import forms
from .models import Payment, Plan


class SubscriptionChoiceForm(forms.Form):
    """Formulaire de choix de formule d'abonnement."""
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(is_active=True).order_by('price'),
        widget=forms.RadioSelect,
        label="Choisissez votre formule",
        empty_label=None,
    )


class PaymentInitForm(forms.ModelForm):
    """Formulaire d'initiation du paiement Mobile Money."""

    class Meta:
        model = Payment
        fields = ['provider', 'phone_number']
        widgets = {
            'provider': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex : 699000000 ou 671000000',
                'maxlength': '9',
            }),
        }
        labels = {
            'provider':     'Opérateur Mobile Money',
            'phone_number': 'Numéro de téléphone Mobile Money',
        }

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number'].strip().replace(' ', '')
        # Validation basique numéros camerounais
        if not phone.isdigit():
            raise forms.ValidationError("Le numéro doit contenir uniquement des chiffres.")
        if len(phone) not in (9, 12):
            raise forms.ValidationError("Numéro invalide (9 chiffres locaux ou 12 avec indicatif).")
        return phone


class PaymentConfirmForm(forms.Form):
    """Formulaire de confirmation manuelle par l'admin."""
    reference   = forms.CharField(
        label="Référence de transaction",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control',
                                      'placeholder': 'Ex: ORANGE-XXXXXXXX'}),
    )
    admin_notes = forms.CharField(
        label="Notes (optionnel)",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
    )


class PaymentRejectForm(forms.Form):
    """Formulaire de rejet par l'admin."""
    reason = forms.CharField(
        label="Raison du rejet",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                     'placeholder': 'Numéro invalide, doublon...'}),
    )
