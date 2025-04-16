# instruments/tests.py

# Importeer eerst de benodigde modules
from django.test import TestCase, Client
from django.urls import reverse, reverse_lazy
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime

# Importeer je modellen en formulieren
from .models import InstrumentSubmission, Submitter, Note
from .forms import InstrumentSubmissionForm, SubmitterFormSet, NoteForm
# Importeer eventueel de opties die je in de view gebruikt
# Zorg dat deze import werkt en de constanten bestaan in views.py
try:
    from .views import EMAIL_OPTIONS, DOWNLOAD_OPTIONS
except ImportError:
    # Definieer dummy waarden als de import faalt (bv. tijdens vroege testfase)
    # zodat tests die ze nodig hebben niet direct crashen op NameError.
    # De tests die de context checken zullen dan mogelijk falen, wat je erop wijst
    # dat de constanten correct gedefinieerd moeten worden in views.py.
    print("Warning: Could not import EMAIL_OPTIONS/DOWNLOAD_OPTIONS from views.py for tests.")
    EMAIL_OPTIONS = []
    DOWNLOAD_OPTIONS = []


# Haal het User model op
User = get_user_model()


# --- Helper Functie (Aangepast) ---
def create_user_and_submission(username_part='testuser', email_domain='@example.com', subject='Test Subject', **user_kwargs):
    """ Helper to create a user and a submission owned by that user. """
    # Ensure unique email to avoid collisions during test runs
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    email = f"{username_part}_{timestamp}{email_domain}"

    # Provide required fields for create_user, crucially 'email'
    # Assume password is required, other fields via user_kwargs
    # DO NOT pass 'username' if email is the USERNAME_FIELD and not expected by CustomUser model
    user = User.objects.create_user(email=email, password='password123', **user_kwargs)

    # Create submission WITH date
    submission = InstrumentSubmission.objects.create(
        owner=user,
        subject=subject,
        date=datetime.date.today() # Datum is hier toegevoegd
    )
    return user, submission


# --- Model Tests (setUp aangepast) ---

class InstrumentSubmissionModelTests(TestCase):

    def setUp(self):
        # Maak een testgebruiker aan MET email, ZONDER username
        # Voeg eventuele andere VERPLICHTE velden van CustomUser toe
        self.user = User.objects.create_user(
            email='test_ism@example.com',
            password='password123',
            # initials='T', # Voeg toe indien verplicht voor jouw CustomUser
            # last_name='User', # Voeg toe indien verplicht
        )
        # Maak een test submission aan MET date
        self.submission = InstrumentSubmission.objects.create(
            owner=self.user,
            subject='Test Onderwerp',
            instrument='Test Instrument',
            date=datetime.date.today(), # Datum was hier al correct
            considerations='Test overwegingen',
            requests='Test verzoeken'
        )

    def test_string_representation(self):
        self.assertEqual(str(self.submission), f"Test Onderwerp ({self.submission.pk})")

    def test_submission_creation(self):
        self.assertEqual(self.submission.owner, self.user)
        self.assertEqual(self.submission.subject, 'Test Onderwerp')
        self.assertTrue(isinstance(self.submission.created_at, datetime.datetime))
        self.assertTrue(isinstance(self.submission.updated_at, datetime.datetime))


class SubmitterModelTests(TestCase):

    def setUp(self):
        # Geef email mee
        self.user = User.objects.create_user(email='test_sm@example.com', password='password123')
        # VOEG 'date' TOE AAN DE CREATE CALL:
        self.submission = InstrumentSubmission.objects.create(
            owner=self.user,
            subject='Sub Test',
            date=datetime.date.today() # <--- TOEGEVOEGD
        )
        self.submitter = Submitter.objects.create(
            submission=self.submission,
            initials='T.',
            lastname='Tester',
            party='Test Partij'
        )

    def test_string_representation(self):
        self.assertEqual(str(self.submitter), "T. Tester (Test Partij)")

    def test_submitter_creation(self):
        self.assertEqual(self.submitter.submission, self.submission)
        self.assertEqual(self.submitter.initials, 'T.')


class NoteModelTests(TestCase):

    def setUp(self):
         # Geef email mee
        self.user = User.objects.create_user(email='test_nm@example.com', password='password123')
         # VOEG 'date' TOE AAN DE CREATE CALL:
        self.submission = InstrumentSubmission.objects.create(
            owner=self.user,
            subject='Note Test',
            date=datetime.date.today() # <--- TOEGEVOEGD
        )
        self.note = Note.objects.create(
            submission=self.submission,
            user=self.user,
            text='Dit is een test notitie.'
        )

    def test_string_representation(self):
        # Gebruik email of een ander relevant veld als username niet bestaat
        identifier = self.user.email if hasattr(self.user, 'email') else str(self.user)
        expected_str = f"Notitie voor '{self.submission.subject}' door {identifier} op {self.note.created_at.strftime('%Y-%m-%d')}"
        self.assertEqual(str(self.note), expected_str)

    def test_note_creation(self):
        self.assertEqual(self.note.submission, self.submission)
        self.assertEqual(self.note.user, self.user)
        self.assertEqual(self.note.text, 'Dit is een test notitie.')


# --- Form Tests ---

class NoteFormTests(TestCase):

    def test_valid_note_form(self):
        form = NoteForm(data={'text': 'Een valide notitie.'})
        self.assertTrue(form.is_valid())

    def test_invalid_note_form_empty(self):
        form = NoteForm(data={'text': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)


class InstrumentSubmissionFormTests(TestCase):

    def test_valid_submission_form(self):
        # Test met valide data
        # CONTROLEER: Zijn er meer verplichte velden op je model/form?
        # Voeg die hier toe indien nodig.
        data = {
            'subject': 'Valide Onderwerp',
            'instrument': 'Valide Instrument',
            'date': datetime.date.today(),
            'considerations': 'Valide overwegingen', # Misschien zijn deze niet verplicht?
            'requests': 'Valide verzoeken'     # Misschien zijn deze niet verplicht?
        }
        form = InstrumentSubmissionForm(data=data)
        # Als dit nog steeds faalt, print de errors om te zien wat er mis is:
        if not form.is_valid():
            print("\n--- DEBUG: InstrumentSubmissionForm Errors ---")
            print(form.errors.as_json(indent=2))
            print("--- END DEBUG ---")
        self.assertTrue(form.is_valid())

    def test_invalid_submission_form_missing_subject(self):
        data = {
            'instrument': 'Valide Instrument',
            'date': datetime.date.today(),
        }
        form = InstrumentSubmissionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('subject', form.errors)

    def test_invalid_submission_form_invalid_date(self):
        data = {
            'subject': 'Valide Onderwerp',
            'instrument': 'Valide Instrument',
            'date': 'geen-datum', # Ongeldig formaat
        }
        form = InstrumentSubmissionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)


class SubmitterFormSetTests(TestCase):

    def setUp(self):
         # Geef email mee
        self.user = User.objects.create_user(email='test_sf@example.com', password='password123')
        # VOEG 'date' TOE AAN DE CREATE CALL:
        self.submission = InstrumentSubmission.objects.create(
            owner=self.user,
            subject='Formset Test',
            date=datetime.date.today() # <--- TOEGEVOEGD
        )

    def test_valid_submitter_formset(self):
        formset_data = {
            'submitters-TOTAL_FORMS': '1',
            'submitters-INITIAL_FORMS': '0',
            'submitters-MIN_NUM_FORMS': '0',
            'submitters-MAX_NUM_FORMS': '10',
            'submitters-0-initials': 'J.',
            'submitters-0-lastname': 'Doe',
            'submitters-0-party': 'Test Partij',
            # 'submitters-0-submission': str(self.submission.pk) # Waarschijnlijk niet nodig in POST data
        }
        # Geef instance mee voor formsets gekoppeld aan bestaand object
        formset = SubmitterFormSet(data=formset_data, instance=self.submission)
        if not formset.is_valid():
             print("\n--- DEBUG: SubmitterFormSet Errors (valid test) ---")
             print(formset.errors)
             print("--- END DEBUG ---")
        self.assertTrue(formset.is_valid())

    def test_invalid_submitter_formset_missing_lastname(self):
        formset_data = {
            'submitters-TOTAL_FORMS': '1',
            'submitters-INITIAL_FORMS': '0',
            'submitters-MIN_NUM_FORMS': '0',
            'submitters-MAX_NUM_FORMS': '10',
            'submitters-0-initials': 'J.',
            'submitters-0-lastname': '', # Leeg veld
            'submitters-0-party': 'Test Partij',
        }
        formset = SubmitterFormSet(data=formset_data, instance=self.submission)
        self.assertFalse(formset.is_valid())
        # Check of er een error is voor het specifieke veld in de eerste form
        self.assertTrue(any('lastname' in field_errors for field_errors in formset.errors[0]))

    def test_submitter_formset_delete(self):
         # Maak eerst een bestaande submitter aan
        submitter = Submitter.objects.create(submission=self.submission, initials='X', lastname='ToDelete')
        formset_data = {
            'submitters-TOTAL_FORMS': '1',
            'submitters-INITIAL_FORMS': '1', # We starten met 1 bestaande form
            'submitters-MIN_NUM_FORMS': '0',
            'submitters-MAX_NUM_FORMS': '10',
            'submitters-0-id': str(submitter.pk), # ID van de bestaande submitter
            'submitters-0-initials': 'X',
            'submitters-0-lastname': 'ToDelete',
            'submitters-0-party': '',
            'submitters-0-DELETE': 'on', # Markeer voor verwijdering
        }
        formset = SubmitterFormSet(data=formset_data, instance=self.submission)
        self.assertTrue(formset.is_valid())
        # Belangrijk: save() verwerkt de verwijdering
        formset.save()
        self.assertFalse(Submitter.objects.filter(pk=submitter.pk).exists())


# --- View Tests ---

class ViewAccessTests(TestCase):
    """ Test toegang tot views (login vereist, permissies) """

    def setUp(self):
        self.client = Client()
        # Gebruik de aangepaste helper, geef eventueel extra user fields mee indien nodig voor CustomUser
        self.user1, self.submission1 = create_user_and_submission('user1', subject='Sub 1', initials='U', lastname='One') # Vb: initials/lastname toegevoegd
        self.user2, self.submission2 = create_user_and_submission('user2', subject='Sub 2', initials='U', lastname='Two') # Vb: initials/lastname toegevoegd
        self.note1 = Note.objects.create(submission=self.submission1, user=self.user1, text='Note 1')

        self.list_url = reverse('instrument_submission_list')
        self.create_url = reverse('instrument_submission_create')
        self.detail_url1 = reverse('instrument_submission_detail', args=[self.submission1.pk])
        self.edit_url1 = reverse('instrument_submission_edit', args=[self.submission1.pk])
        self.delete_url1 = reverse('instrument_submission_delete', args=[self.submission1.pk])
        self.detail_url2 = reverse('instrument_submission_detail', args=[self.submission2.pk]) # Van andere user
        self.edit_url2 = reverse('instrument_submission_edit', args=[self.submission2.pk])     # Van andere user
        self.delete_url2 = reverse('instrument_submission_delete', args=[self.submission2.pk]) # Van andere user
        self.note_edit_url1 = reverse('note_edit', args=[self.note1.pk])
        self.note_delete_url1 = reverse('note_delete', args=[self.note1.pk])

        # Gebruik email om in te loggen als dat je USERNAME_FIELD is
        self.user1_login_credential = self.user1.email
        self.user2_login_credential = self.user2.email
        self.login_url = reverse('accounts:login') # Aanname van URL naam

    def test_login_required_views(self):
        urls_to_test = [
            self.list_url, self.create_url, self.detail_url1, self.edit_url1,
            self.delete_url1, self.note_edit_url1, self.note_delete_url1
        ]
        for url in urls_to_test:
            response = self.client.get(url)
            # Standaard login URL kan verschillen, pas evt. aan
            self.assertRedirects(response, f"{self.login_url}?next={url}")

    def test_owner_required_views_get(self):
        # Gebruik email om in te loggen
        logged_in = self.client.login(email=self.user2_login_credential, password='password123')
        self.assertTrue(logged_in, "Inloggen voor test_owner_required_views_get mislukt") # Check of login succesvol was

        urls_to_test_404 = [self.detail_url1, self.edit_url1, self.delete_url1]
        urls_to_test_403 = [self.note_edit_url1, self.note_delete_url1]

        for url in urls_to_test_404:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404, f"Verwachte 404 voor GET {url}, kreeg {response.status_code}")

        for url in urls_to_test_403:
             response = self.client.get(url)
             self.assertEqual(response.status_code, 403, f"Verwachte 403 voor GET {url}, kreeg {response.status_code}")

        self.client.logout()

    def test_owner_required_views_post(self):
        logged_in = self.client.login(email=self.user2_login_credential, password='password123')
        self.assertTrue(logged_in, "Inloggen voor test_owner_required_views_post mislukt")

        # Probeer notitie te posten op submission van user1
        response = self.client.post(self.detail_url1, {'text': 'Poging tot hack notitie'})
        self.assertEqual(response.status_code, 404, f"Verwachte 404 voor POST note op {self.detail_url1}, kreeg {response.status_code}")

        # Probeer submission 1 te verwijderen
        response = self.client.post(self.delete_url1)
        self.assertEqual(response.status_code, 404, f"Verwachte 404 voor POST delete op {self.delete_url1}, kreeg {response.status_code}")

         # Probeer notitie 1 te verwijderen
        response = self.client.post(self.note_delete_url1)
        self.assertEqual(response.status_code, 403, f"Verwachte 403 voor POST delete op {self.note_delete_url1}, kreeg {response.status_code}")

        self.client.logout()


class InstrumentSubmissionListViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user, self.submission1 = create_user_and_submission('user1', subject='Sub A')
        self.submission2 = InstrumentSubmission.objects.create(owner=self.user, subject='Sub B', date=datetime.date.today() - datetime.timedelta(days=1))
        self.other_user, self.other_submission = create_user_and_submission('user2', subject='Other Sub')
        self.list_url = reverse('instrument_submission_list')
        # Gebruik email om in te loggen
        self.client.login(email=self.user.email, password='password123')

    def test_list_view_uses_correct_template(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'instruments/submission_list.html')

    def test_list_view_shows_only_owner_submissions(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sub A')
        self.assertContains(response, 'Sub B')
        self.assertNotContains(response, 'Other Sub') # Mag submission van andere user niet tonen

    def test_list_view_pagination(self):
        # Maak meer submissions aan dan paginate_by (aanname: 10 in view)
        for i in range(15):
            # Gebruik de helper, evt. met extra data voor unieke email
            create_user_and_submission(username_part=f'user1_page_{i}', subject=f'Sub {i+2}', owner_user=self.user)


        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        # Pas het verwachte aantal aan op basis van je paginate_by (10)
        self.assertEqual(len(response.context['submissions']), 10) # Check aantal op eerste pagina

        # Test toegang tot tweede pagina
        response_page2 = self.client.get(self.list_url + '?page=2')
        self.assertEqual(response_page2.status_code, 200)
        self.assertTrue(response_page2.context['is_paginated'])
        # We hadden er 2 + 15 = 17. Pagina 2 heeft 7.
        self.assertEqual(len(response_page2.context['submissions']), 7)

    def test_list_view_filtering(self):
        # Test filteren op onderwerp
        response = self.client.get(self.list_url + '?q=Sub+A')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sub A')
        self.assertNotContains(response, 'Sub B')

    def test_list_view_sorting(self):
        # Test sorteren op onderwerp (oplopend)
        response = self.client.get(self.list_url + '?sort=subject')
        self.assertEqual(response.status_code, 200)
        # Aanname: Sub A komt voor Sub B in de context lijst
        submissions_in_context = list(response.context['submissions'])
        # Wees voorzichtig met index-gebaseerde checks als volgorde niet 100% vastligt
        subjects = [s.subject for s in submissions_in_context]
        self.assertListEqual(sorted(subjects), subjects) # Check of het gesorteerd is

        # Test sorteren op onderwerp (aflopend)
        response = self.client.get(self.list_url + '?sort=subject_desc')
        self.assertEqual(response.status_code, 200)
        submissions_in_context = list(response.context['submissions'])
        subjects = [s.subject for s in submissions_in_context]
        self.assertListEqual(sorted(subjects, reverse=True), subjects) # Check of het omgekeerd gesorteerd is

    def test_list_view_context_options(self):
        # Test of de export opties in de context zitten
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('email_export_options', response.context)
        self.assertEqual(response.context['email_export_options'], EMAIL_OPTIONS) # Vergelijk met de constante
        self.assertIn('download_export_options', response.context)
        self.assertEqual(response.context['download_export_options'], DOWNLOAD_OPTIONS)


class InstrumentSubmissionCreateViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        # Geef email mee
        self.user = User.objects.create_user(email='test_create@example.com', password='password123')
        self.create_url = reverse('instrument_submission_create')
        # Gebruik email om in te loggen
        self.client.login(email='test_create@example.com', password='password123')

    def test_create_view_get(self):
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'instruments/submission_form.html')
        self.assertIn('form', response.context)
        self.assertIn('submitter_formset', response.context)

    def test_create_view_post_valid(self):
        post_data = {
            'subject': 'Nieuw Onderwerp',
            'instrument': 'Nieuw Instrument',
            'date': datetime.date.today(),
            'considerations': 'Nieuwe overwegingen',
            'requests': 'Nieuwe verzoeken',
            # Formset data
            'submitters-TOTAL_FORMS': '1',
            'submitters-INITIAL_FORMS': '0',
            'submitters-MIN_NUM_FORMS': '0',
            'submitters-MAX_NUM_FORMS': '10',
            'submitters-0-initials': 'N.',
            'submitters-0-lastname': 'Persoon',
            'submitters-0-party': 'Nieuw',
            'submit_action': 'save_return', # Belangrijk voor redirect check
        }
        response = self.client.post(self.create_url, post_data)
        # Check of object is aangemaakt
        self.assertTrue(InstrumentSubmission.objects.filter(subject='Nieuw Onderwerp').exists())
        submission = InstrumentSubmission.objects.get(subject='Nieuw Onderwerp')
        # Check of eigenaar correct is ingesteld
        self.assertEqual(submission.owner, self.user)
        # Check of submitter is aangemaakt
        self.assertEqual(submission.submitters.count(), 1)
        self.assertEqual(submission.submitters.first().lastname, 'Persoon')
        # Check redirect naar detail pagina
        self.assertRedirects(response, reverse('instrument_submission_detail', args=[submission.pk]))

    def test_create_view_post_valid_save_stay(self):
        # Test POST met valide data en 'save_stay' actie
        post_data = {
            'subject': 'Nog een Onderwerp',
            'instrument': 'Nog een Instrument',
            'date': datetime.date.today(),
            # Formset data
            'submitters-TOTAL_FORMS': '0', # Geen indieners deze keer
            'submitters-INITIAL_FORMS': '0',
            'submitters-MIN_NUM_FORMS': '0',
            'submitters-MAX_NUM_FORMS': '10',
            'submit_action': 'save_stay', # Andere actie
        }
        response = self.client.post(self.create_url, post_data)
        self.assertTrue(InstrumentSubmission.objects.filter(subject='Nog een Onderwerp').exists())
        submission = InstrumentSubmission.objects.get(subject='Nog een Onderwerp')
        # Check redirect naar edit pagina
        self.assertRedirects(response, reverse('instrument_submission_edit', args=[submission.pk]))


    def test_create_view_post_invalid(self):
        # Test POST met invalide data (ontbrekend onderwerp)
        post_data = {
            'instrument': 'Invalide Instrument',
            'date': datetime.date.today(),
            # Formset data (ook al is die leeg, management is nodig)
            'submitters-TOTAL_FORMS': '0',
            'submitters-INITIAL_FORMS': '0',
            'submitters-MIN_NUM_FORMS': '0',
            'submitters-MAX_NUM_FORMS': '10',
        }
        response = self.client.post(self.create_url, post_data)
        # Moet op dezelfde pagina blijven en errors tonen
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'instruments/submission_form.html')
        self.assertFormError(response, 'form', 'subject', 'Dit veld is vereist.')
        # Check dat er geen object is aangemaakt
        self.assertFalse(InstrumentSubmission.objects.filter(instrument='Invalide Instrument').exists())


class InstrumentSubmissionDetailViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        # Geef email mee
        self.user, self.submission = create_user_and_submission('user1', subject='Detail Test')
        self.note = Note.objects.create(submission=self.submission, user=self.user, text='Test notitie')
        self.detail_url = reverse('instrument_submission_detail', args=[self.submission.pk])
        # Gebruik email om in te loggen
        self.client.login(email=self.user.email, password='password123')

    def test_detail_view_get(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'instruments/submission_detail.html')
        self.assertContains(response, 'Detail Test') # Onderwerp
        self.assertContains(response, 'Test notitie') # Notitie
        self.assertIn('object', response.context)
        self.assertEqual(response.context['object'], self.submission)
        self.assertIn('preview', response.context) # Check of preview context bestaat
        self.assertIn('note_form', response.context)
        self.assertIn('notes', response.context)
        self.assertIn('download_export_options', response.context) # Check export opties
        self.assertIn('email_export_options', response.context)

    def test_detail_view_post_note_valid(self):
        # Test het posten van een valide notitie
        note_data = {'text': 'Nieuwe notitie via detail view'}
        # We moeten follow=True gebruiken omdat de POST view redirect
        response = self.client.post(self.detail_url, note_data, follow=True)
        # Check of we terug zijn op de detail pagina (status 200 na redirect)
        self.assertEqual(response.status_code, 200)
        # Check of de nieuwe notitie nu zichtbaar is
        self.assertContains(response, 'Nieuwe notitie via detail view')
        # Check ook de database
        self.assertTrue(Note.objects.filter(text='Nieuwe notitie via detail view', submission=self.submission).exists())
        new_note = Note.objects.get(text='Nieuwe notitie via detail view')
        self.assertEqual(new_note.submission, self.submission)
        self.assertEqual(new_note.user, self.user)

    def test_detail_view_post_note_invalid(self):
        # Test het posten van een invalide notitie (leeg)
        note_data = {'text': ''}
        initial_note_count = Note.objects.filter(submission=self.submission).count()
        response = self.client.post(self.detail_url, note_data)
        # Moet redirecten naar dezelfde pagina (want post logic zit in aparte view class)
        self.assertRedirects(response, self.detail_url)
         # Check dat er geen nieuwe notitie is aangemaakt
        self.assertEqual(Note.objects.filter(submission=self.submission).count(), initial_note_count)


class InstrumentSubmissionUpdateViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        # Geef email mee en eventueel andere vereiste velden
        self.user, self.submission = create_user_and_submission('user1', subject='Update Test', initials='U', lastname='One')
        self.submitter = Submitter.objects.create(submission=self.submission, initials='I', lastname='Voor')
        self.edit_url = reverse('instrument_submission_edit', args=[self.submission.pk])
        self.detail_url = reverse('instrument_submission_detail', args=[self.submission.pk])
        # Gebruik email om in te loggen
        self.client.login(email=self.user.email, password='password123')

    def test_update_view_get(self):
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'instruments/submission_form.html')
        self.assertIn('form', response.context)
        self.assertIn('submitter_formset', response.context)
        # Check of het formulier de bestaande data bevat
        self.assertEqual(response.context['form'].initial['subject'], 'Update Test')
        # Check of formset de bestaande submitter bevat
        # Let op: initial_forms is een lijst
        self.assertTrue(len(response.context['submitter_formset'].initial_forms) > 0)
        self.assertEqual(response.context['submitter_formset'].initial_forms[0].initial['lastname'], 'Voor')


    def test_update_view_post_valid(self):
        # Test POST met valide data om te updaten
        post_data = {
            'subject': 'Geüpdatet Onderwerp', # Gewijzigd
            'instrument': 'Geüpdatet Instrument', # Gewijzigd
            'date': self.submission.date, # Behoud datum
            'considerations': 'Updated considerations',
            'requests': 'Updated requests',
            # Formset data - update bestaande, voeg nieuwe toe, verwijder geen
            'submitters-TOTAL_FORMS': '2', # Nu 2 formulieren
            'submitters-INITIAL_FORMS': '1', # 1 bestond al
            'submitters-MIN_NUM_FORMS': '0',
            'submitters-MAX_NUM_FORMS': '10',
            # Form 0 (bestaande)
            'submitters-0-id': str(self.submitter.pk),
            'submitters-0-initials': 'I.', # Gewijzigd
            'submitters-0-lastname': 'Na', # Gewijzigd
            'submitters-0-party': 'Update',
            # Form 1 (nieuwe)
            'submitters-1-initials': 'N.',
            'submitters-1-lastname': 'Nieuw',
            'submitters-1-party': 'Extra',
            'submit_action': 'save_return',
        }
        response = self.client.post(self.edit_url, post_data)

        # Check redirect naar detail pagina
        # Controleer eerst of er form errors zijn voor debuggen
        if response.status_code != 302:
            form_errors = response.context.get('form', None).errors if response.context else None
            formset_errors = response.context.get('submitter_formset', None).errors if response.context else None
            print("\n--- DEBUG: UpdateView POST Errors ---")
            if form_errors: print("Form Errors:", form_errors.as_json(indent=2))
            if formset_errors: print("Formset Errors:", formset_errors)
            print("--- END DEBUG ---")

        self.assertRedirects(response, self.detail_url, msg_prefix="Redirect failed in test_update_view_post_valid")

        # Haal het object opnieuw op en check de wijzigingen
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.subject, 'Geüpdatet Onderwerp')
        self.assertEqual(self.submission.instrument, 'Geüpdatet Instrument')

        # Check submitters
        self.assertEqual(self.submission.submitters.count(), 2)
        updated_submitter = self.submission.submitters.get(pk=self.submitter.pk)
        self.assertEqual(updated_submitter.initials, 'I.')
        self.assertEqual(updated_submitter.lastname, 'Na')
        new_submitter_qs = self.submission.submitters.filter(lastname='Nieuw')
        self.assertTrue(new_submitter_qs.exists())
        self.assertEqual(new_submitter_qs.first().initials, 'N.')


class InstrumentSubmissionDeleteViewTests(TestCase):

    def setUp(self):
        self.client = Client()
         # Geef email mee
        self.user, self.submission = create_user_and_submission('user1', subject='Delete Test')
        self.delete_url = reverse('instrument_submission_delete', args=[self.submission.pk])
        self.list_url = reverse('instrument_submission_list')
         # Gebruik email om in te loggen
        self.client.login(email=self.user.email, password='password123')

    def test_delete_view_get(self):
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'instruments/submission_confirm_delete.html')
        self.assertContains(response, 'Delete Test') # Check of onderwerp wordt getoond

    def test_delete_view_post(self):
        response = self.client.post(self.delete_url)
        # Check redirect naar lijst pagina
        self.assertRedirects(response, self.list_url)
        # Check of het object daadwerkelijk verwijderd is
        self.assertFalse(InstrumentSubmission.objects.filter(pk=self.submission.pk).exists())


class NoteUpdateViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Geef email mee
        self.user, self.submission = create_user_and_submission('user1', subject='Note Update Test')
        self.note = Note.objects.create(submission=self.submission, user=self.user, text='Originele notitie')
        self.edit_url = reverse('note_edit', args=[self.note.pk])
        self.detail_url = reverse('instrument_submission_detail', args=[self.submission.pk])
        # Gebruik email om in te loggen
        self.client.login(email=self.user.email, password='password123')

    def test_note_update_view_get(self):
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'instruments/note_form.html')
        self.assertEqual(response.context['form'].initial['text'], 'Originele notitie')

    def test_note_update_view_post(self):
        post_data = {'text': 'Gewijzigde notitie'}
        response = self.client.post(self.edit_url, post_data)
        self.assertRedirects(response, self.detail_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, 'Gewijzigde notitie')


class NoteDeleteViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Geef email mee
        self.user, self.submission = create_user_and_submission('user1', subject='Note Delete Test')
        self.note = Note.objects.create(submission=self.submission, user=self.user, text='Te verwijderen notitie')
        self.delete_url = reverse('note_delete', args=[self.note.pk])
        self.detail_url = reverse('instrument_submission_detail', args=[self.submission.pk])
        # Gebruik email om in te loggen
        self.client.login(email=self.user.email, password='password123')

    def test_note_delete_view_get(self):
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'instruments/note_confirm_delete.html')
        self.assertContains(response, 'Te verwijderen notitie')

    def test_note_delete_view_post(self):
        response = self.client.post(self.delete_url)
        self.assertRedirects(response, self.detail_url)
        self.assertFalse(Note.objects.filter(pk=self.note.pk).exists())