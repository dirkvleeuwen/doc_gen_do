from django.db import models
from django.conf import settings
from instruments.models import InstrumentSubmission, InstrumentVersion
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class ApprovalStatus(models.TextChoices):
    PENDING = 'pending', _('In behandeling')
    APPROVED = 'approved', _('Goedgekeurd')
    REJECTED = 'rejected', _('Afgewezen')

class ApprovalGroup(models.Model):
    """Groep gebruikers die als aparte eenheid goedkeuring kan geven"""
    name = models.CharField(max_length=100, verbose_name=_('Naam'))
    description = models.TextField(blank=True, verbose_name=_('Beschrijving'))
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="approval_groups",
        verbose_name=_('Leden')
    )
    
    class Meta:
        verbose_name = _('Goedkeuringsgroep')
        verbose_name_plural = _('Goedkeuringsgroepen')
    
    def __str__(self):
        return self.name

class ApprovalRequest(models.Model):
    """Model to track approval requests for instrument submissions"""
    submission = models.ForeignKey(
        InstrumentSubmission,
        on_delete=models.CASCADE,
        related_name='approval_requests'
    )
    version = models.ForeignKey(
        InstrumentVersion,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approval_requests'
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_approvals'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_approvals'
    )
    status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING
    )
    required_groups = models.ManyToManyField(
        ApprovalGroup,
        related_name="assigned_requests",
        verbose_name=_('Vereiste goedkeuringsgroepen'),
        help_text=_('Groepen die dit verzoek moeten goedkeuren')
    )
    request_comment = models.TextField(blank=True, help_text=_('Toelichting van de aanvrager bij het verzoek'))
    review_comment = models.TextField(blank=True, help_text=_('Commentaar van de beoordelaar bij goed- of afkeuring'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        get_latest_by = 'created_at'
        verbose_name = _('Goedkeuringsverzoek')
        verbose_name_plural = _('Goedkeuringsverzoeken')

    def __str__(self):
        return f"Goedkeuring {self.submission} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Create a new version when creating a new approval request
        if not self.pk and not self.version:
            self.version = InstrumentVersion.create_from_submission(self.submission)
        super().save(*args, **kwargs)
    
    def update_status_based_on_group_approvals(self):
        """Update de status op basis van de ontvangen groepsgoedkeuringen"""
        group_approvals = self.group_approvals.all()
        
        # Als er minstens één afwijzing is, wordt het verzoek afgewezen
        if group_approvals.filter(status='REJECTED').exists():
            self.status = 'REJECTED'
            self.reviewed_at = timezone.now()
            self.save()
            return
        
        # Controleer of alle vereiste groepen hebben goedgekeurd
        required_groups_count = self.required_groups.count()
        approved_groups_count = group_approvals.filter(status='APPROVED').count()
        
        # Goedkeuring alleen als alle vereiste groepen volledig hebben goedgekeurd
        if approved_groups_count >= required_groups_count and required_groups_count > 0:
            self.status = 'APPROVED'
            self.reviewed_at = timezone.now()
            self.save()
    
    def initialize_group_approvals(self):
        """Maak GroupApproval objecten aan voor alle vereiste groepen"""
        for group in self.required_groups.all():
            GroupApproval.objects.get_or_create(
                approval_request=self,
                group=group,
                defaults={'status': 'PENDING'}
            )
    
    def can_user_review(self, user):
        """Controleer of een gebruiker dit verzoek mag beoordelen"""
        # Aanvrager mag niet zijn eigen verzoek beoordelen
        if self.requester == user:
            return False
        
        # Controleer of de gebruiker lid is van een vereiste groep die nog niet heeft gestemd
        pending_groups = self.group_approvals.filter(status='PENDING').values_list('group', flat=True)
        user_groups = user.approval_groups.filter(pk__in=pending_groups)
        
        return user_groups.exists()

class GroupApproval(models.Model):
    """Model voor goedkeuringen door groepen voor één aanvraag"""
    approval_request = models.ForeignKey(
        ApprovalRequest, 
        on_delete=models.CASCADE,
        related_name="group_approvals",
        verbose_name=_('Goedkeuringsverzoek')
    )
    group = models.ForeignKey(
        ApprovalGroup,
        on_delete=models.CASCADE,
        related_name="approvals",
        verbose_name=_('Groep')
    )
    status = models.CharField(
        max_length=10,
        choices=[
            ('PENDING', _('In afwachting')), 
            ('APPROVED', _('Goedgekeurd')), 
            ('REJECTED', _('Afgekeurd'))
        ],
        default='PENDING',
        verbose_name=_('Status')
    )
    # Dit veld wordt nu gebruikt om bij te houden welke gebruiker de LAATSTE actie heeft uitgevoerd
    # en wordt gebruikt voor logging en weergave
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="group_approvals",
        verbose_name=_('Beoordelaar')
    )
    review_comment = models.TextField(
        blank=True, 
        verbose_name=_('Commentaar'),
        help_text=_('Commentaar van de beoordelaar bij goed- of afkeuring')
    )
    reviewed_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name=_('Beoordeeld op')
    )
    
    # Nieuwe velden
    # Een ManyToMany veld om bij te houden welke gebruikers binnen de groep akkoord hebben gegeven
    approved_members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="approved_group_approvals",
        verbose_name=_('Leden die hebben goedgekeurd'),
        blank=True
    )
    # Een ManyToMany veld om bij te houden welke gebruikers binnen de groep hebben afgewezen
    rejected_members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="rejected_group_approvals",
        verbose_name=_('Leden die hebben afgewezen'),
        blank=True
    )
    
    class Meta:
        unique_together = ('approval_request', 'group')
        verbose_name = _('Groepsgoedkeuring')
        verbose_name_plural = _('Groepsgoedkeuringen')
    
    def __str__(self):
        return f"Beoordeling door {self.group.name} voor verzoek {self.approval_request.pk}: {self.get_status_display()}"
    
    def check_all_members_approved(self):
        """Controleert of alle leden van de groep hebben goedgekeurd (exclusief de aanvrager)"""
        # Bepaal het totale aantal leden dat mag stemmen (totaal leden minus aanvrager indien aanwezig)
        total_voting_members = self.group.members.count()
        requester = self.approval_request.requester
        
        # Als de aanvrager lid is van de groep, tel deze niet mee
        if requester in self.group.members.all():
            total_voting_members -= 1
            
        # Alle stemgerechtigde leden hebben goedgekeurd als het aantal goedkeuringen gelijk is aan
        # het aantal stemgerechtigde leden (en er zijn stemgerechtigde leden)
        approved_count = self.approved_members.count()
        return total_voting_members > 0 and approved_count >= total_voting_members
        
    def update_status(self):
        """Update de status op basis van de goedkeuringen van groepsleden"""
        # Als er een afwijzing is, is de groep afgewezen
        if self.rejected_members.exists():
            self.status = 'REJECTED'
            self.save()
            return
        
        # Als alle leden hebben goedgekeurd, is de groep goedgekeurd
        if self.check_all_members_approved():
            self.status = 'APPROVED'
            self.save()
            return

    def can_user_vote(self, user):
        """Controleert of een gebruiker mag stemmen voor deze groep
        
        Een gebruiker mag stemmen als:
        1. De gebruiker lid is van de groep
        2. De gebruiker niet de aanvrager is van het verzoek
        3. De gebruiker nog niet heeft gestemd voor deze groep
        """
        # Controleer of gebruiker lid is van de groep
        if user not in self.group.members.all():
            return False
        
        # Controleer of gebruiker niet de aanvrager is
        if user == self.approval_request.requester:
            return False
        
        # Controleer of gebruiker nog niet heeft gestemd
        already_voted = (user in self.approved_members.all() or 
                        user in self.rejected_members.all())
        if already_voted:
            return False
            
        return True

class ApprovalLog(models.Model):
    """Model to track approval workflow history"""
    approval = models.ForeignKey(
        ApprovalRequest,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    action = models.CharField(max_length=50)  # e.g. "submitted", "approved", "rejected"
    comment = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = _('Goedkeuringslog')
        verbose_name_plural = _('Goedkeuringslogs')

    def __str__(self):
        return f"{self.action} door {self.user} op {self.timestamp}"