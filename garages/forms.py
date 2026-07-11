# garages/forms.py
from django import forms
from .models import Garage

class GarageCreateForm(forms.ModelForm):
    class Meta:
        model = Garage
        fields = [
            'name', 'description', 'address', 'city', 'zip_code',
            'latitude', 'longitude', 'phone_number', 'website', 
            'opening_hours', 'is_open'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nom de votre garage *',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Décrivez vos services, spécialités, équipements...'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Adresse complète *',
                'required': True
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ville *',
                'required': True
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Code postal *',
                'required': True
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Téléphone (ex: +237 6XX XX XX XX)'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control', 
                'placeholder': 'https://votre-site.com'
            }),
            'opening_hours': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'Ex: Lun-Ven: 8h-18h, Sam: 8h-12h'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': 'any', 
                'placeholder': '3.8607',
                'required': True
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': 'any', 
                'placeholder': '11.5205',
                'required': True
            }),
            'is_open': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Nom du garage *',
            'description': 'Description',
            'address': 'Adresse *',
            'city': 'Ville *',
            'zip_code': 'Code postal *',
            'phone_number': 'Téléphone',
            'website': 'Site web',
            'opening_hours': 'Horaires d\'ouverture',
            'latitude': 'Latitude *',
            'longitude': 'Longitude *',
            'is_open': 'Ouvert actuellement',
        }
        help_texts = {
            'latitude': 'Clic droit sur Google Maps → Coordonnées',
            'longitude': 'Format décimal (ex: 3.8607)',
            'is_open': 'Décochez si votre garage est temporairement fermé',
        }

    def clean_latitude(self):
        lat = self.cleaned_data.get('latitude')
        if lat and (lat < -90 or lat > 90):
            raise forms.ValidationError("Latitude invalide (doit être entre -90 et 90)")
        return lat

    def clean_longitude(self):
        lon = self.cleaned_data.get('longitude')
        if lon and (lon < -180 or lon > 180):
            raise forms.ValidationError("Longitude invalide (doit être entre -180 et 180)")
        return lon

class GarageEditForm(forms.ModelForm):
    """
    Formulaire de modification du profil garage.
    Même champs que la création, logo et bannière en plus.
    La latitude/longitude peut être mise à jour via Nominatim côté JS.
    """
    class Meta:
        model = Garage
        fields = [
            'name', 'description', 'address', 'city', 'zip_code',
            'latitude', 'longitude', 'phone_number', 'website',
            'opening_hours', 'is_open', 'logo', 'banner',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Nom du garage *'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3}),
            'address': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Adresse complète *'}),
            'city': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Ville *'}),
            'zip_code': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Code postal *'}),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '+237 6XX XX XX XX'}),
            'website': forms.URLInput(attrs={
                'class': 'form-control', 'placeholder': 'https://...'}),
            'opening_hours': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'Ex: Lun-Ven 8h-18h, Sam 8h-12h'}),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control', 'step': 'any'}),
            'is_open': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'banner': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Nom du garage *',
            'description': 'Description',
            'address': 'Adresse *',
            'city': 'Ville *',
            'zip_code': 'Code postal *',
            'phone_number': 'Téléphone',
            'website': 'Site web',
            'opening_hours': "Horaires d'ouverture",
            'latitude': 'Latitude *',
            'longitude': 'Longitude *',
            'is_open': 'Ouvert actuellement',
            'logo': 'Logo du garage',
            'banner': 'Bannière',
        }

    def clean_latitude(self):
        lat = self.cleaned_data.get('latitude')
        if lat is not None and (lat < -90 or lat > 90):
            raise forms.ValidationError("Latitude invalide (entre -90 et 90)")
        return lat

    def clean_longitude(self):
        lon = self.cleaned_data.get('longitude')
        if lon is not None and (lon < -180 or lon > 180):
            raise forms.ValidationError("Longitude invalide (entre -180 et 180)")
        return lon
