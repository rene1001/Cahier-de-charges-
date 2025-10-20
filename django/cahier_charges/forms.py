
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import CahierCharges, TypeProjet

class CahierChargesForm(forms.ModelForm):
    class Meta:
        model = CahierCharges
        fields = '__all__'
        exclude = ['date_creation']
        widgets = {
            'nom_projet': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Entrez le nom de votre projet',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Décrivez votre projet en détail...',
                'required': True
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Budget estimé en euros'
            }),
            'delai': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 3 mois, 6 semaines...'
            }),
            'fonctionnalites': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Listez les principales fonctionnalités souhaitées...'
            }),
            'technologies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Technologies préférées ou imposées...'
            }),
            'public_cible': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Décrivez votre audience cible...'
            }),
            'contraintes_techniques': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Contraintes techniques particulières...'
            }),
            'type_ia': forms.Select(attrs={'class': 'form-select'}),
            'donnees_requises': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Types de données nécessaires pour l\'IA...'
            }),
            'performance_attendue': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Niveau de performance souhaité...'
            }),
            'date_mariage': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'lieu_mariage': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Lieu de la cérémonie'
            }),
            'nombre_invites': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Nombre d\'invités'
            }),
            'style_mariage': forms.Select(attrs={'class': 'form-select'}),
            'services_requis': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Services souhaités (traiteur, DJ, photographe...)...'
            }),
            'type_construction': forms.Select(attrs={'class': 'form-select'}),
            'surface': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Surface en m²'
            }),
            'localisation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adresse ou zone géographique'
            }),
            'materiaux': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Matériaux souhaités ou imposés...'
            }),
            'normes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Normes et réglementations à respecter...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.type_projet = kwargs.pop('type_projet', None)
        super().__init__(*args, **kwargs)
        
        if self.type_projet:
            self.fields['type_projet'].initial = self.type_projet
            self.fields['type_projet'].widget = forms.HiddenInput()
            
            # Masquer les champs non pertinents selon le type de projet
            self._configure_fields_for_project_type()

    def clean_nom_projet(self):
        nom_projet = self.cleaned_data.get('nom_projet')
        if nom_projet and len(nom_projet) < 3:
            raise forms.ValidationError('Le nom du projet doit contenir au moins 3 caractères.')
        return nom_projet

    def clean_budget(self):
        budget = self.cleaned_data.get('budget')
        if budget is not None and budget < 0:
            raise forms.ValidationError('Le budget ne peut pas être négatif.')
        return budget

    def clean_nombre_invites(self):
        nombre_invites = self.cleaned_data.get('nombre_invites')
        if nombre_invites is not None and nombre_invites < 1:
            raise forms.ValidationError('Le nombre d\'invités doit être d\'au moins 1.')
        return nombre_invites

    def _configure_fields_for_project_type(self):
        """Configure les champs visibles selon le type de projet"""
        base_fields = ['type_projet', 'nom_projet', 'description', 'budget', 'delai']
        
        if self.type_projet in ['site_web', 'app_mobile']:
            visible_fields = base_fields + [
                'fonctionnalites', 'technologies', 'public_cible', 'contraintes_techniques'
            ]
        elif self.type_projet == 'ia':
            visible_fields = base_fields + [
                'type_ia', 'donnees_requises', 'performance_attendue', 'contraintes_techniques'
            ]
        elif self.type_projet == 'mariage':
            visible_fields = base_fields + [
                'date_mariage', 'lieu_mariage', 'nombre_invites', 'style_mariage', 'services_requis'
            ]
        elif self.type_projet == 'construction':
            visible_fields = base_fields + [
                'type_construction', 'surface', 'localisation', 'materiaux', 'normes'
            ]
        else:
            visible_fields = base_fields

        # Masquer tous les champs non pertinents
        for field_name in self.fields:
            if field_name not in visible_fields:
                self.fields[field_name].widget = forms.HiddenInput()
                self.fields[field_name].required = False

class UtilisateurForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(required=True, label='Prénom')
    last_name = forms.CharField(required=True, label='Nom')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user
