import pytest
from django.contrib.auth import get_user_model
from instruments.models import InstrumentSubmission, Note
from datetime import date

User = get_user_model()

@pytest.mark.django_db
def test_instrumentsubmission_str():
    # Maak een dummy user en een submission met vaste datum
    user = User.objects.create_user(username="tester", password="secret")
    sub = InstrumentSubmission.objects.create(
        owner=user,
        instrument="Guitar",
        subject="My test",
        date=date(2025, 4, 19),
    )
    # __str__ is gedefinieerd als "<instrument> - <subject> (<date>)"
    assert str(sub) == "Guitar - My test (2025-04-19)"


@pytest.mark.django_db
def test_note_str():
    user = User.objects.create_user(username="note_tester", password="secret")
    # eerst een submission nodig, anders foreign key failure
    sub = InstrumentSubmission.objects.create(
        owner=user,
        instrument="Piano",
        subject="Note test",
        date=date.today(),
    )
    note = Note.objects.create(
        submission=sub,
        user=user,
        text="Dit is een notitie",
    )
    # __str__ bevat "Notitie door <user> op <YYYY-MM-DD>"
    txt = str(note)
    assert "Notitie door note_tester op " in txt
