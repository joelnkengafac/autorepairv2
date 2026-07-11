from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    """Formulaire pour laisser un avis"""
    
    # Widget personnalisé pour les étoiles (sera géré par JS)
    rating = forms.IntegerField(
        label="Votre note",
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'type': 'range',
            'min': 1,
            'max': 5,
            'step': 1,
            'class': 'form-range rating-input',
            'id': 'ratingInput'
        })
    )
    
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de votre avis (optionnel)',
                'maxlength': 100
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Décrivez votre expérience : qualité du service, accueil, prix, délais...',
                'rows': 4,
                'maxlength': 1000
            }),
        }
        labels = {
            'comment': 'Votre commentaire *',
        }
        help_texts = {
            'comment': 'Votre avis aide les autres clients à choisir.',
        }
    
    def clean_comment(self):
        """Valider que le commentaire n'est pas trop court"""
        comment = self.cleaned_data.get('comment')
        if len(comment.strip()) < 10:
            raise forms.ValidationError("Votre commentaire doit contenir au moins 10 caractères.")
        return comment