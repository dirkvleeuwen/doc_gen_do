from django.views.generic import ListView, DetailView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Exists, OuterRef
from django.http import Http404
from instruments.models import InstrumentSubmission
from .models import ApprovalRequest, ApprovalLog
from .forms import ApprovalRequestForm, ReviewForm
from itertools import groupby
from operator import attrgetter
from . import is_enabled


class ApprovalFeatureRequiredMixin:
    """
    Mixin die controleert of de approvals functionaliteit is ingeschakeld.
    Redirect naar homepage of raise 404 als functionaliteit is uitgeschakeld.
    """
    def dispatch(self, request, *args, **kwargs):
        if not is_enabled():
            raise Http404("Deze functionaliteit is momenteel niet beschikbaar.")
        return super().dispatch(request, *args, **kwargs)


class ApprovalBaseMixin(ApprovalFeatureRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin):
    """Base mixin for approval views that require authentication and permissions"""
    permission_required = 'approvals.can_review_submissions'

class ApprovalDashboardView(ApprovalBaseMixin, ListView):
    """Dashboard showing all approval requests with filtering options"""
    model = ApprovalRequest
    template_name = 'approvals/dashboard.html'
    context_object_name = 'requests'
    paginate_by = 10

    def get_queryset(self):
        tab = self.request.GET.get('tab', 'pending')
        user = self.request.user
        
        if (tab == 'reviewed'):
            # Haal alle beoordeelde aanvragen op, gesorteerd op submission en datum
            reviewed = ApprovalRequest.objects.exclude(status='PENDING').select_related(
                'submission', 'requester'
            ).prefetch_related('group_approvals', 'group_approvals__group', 'group_approvals__reviewer').order_by('submission', '-reviewed_at')
            
            # Groepeer de aanvragen per submission
            grouped_requests = []
            for submission_id, requests in groupby(reviewed, key=lambda x: x.submission_id):
                requests = list(requests)  # Convert iterator to list
                grouped_requests.append({
                    'submission': requests[0].submission,  # Eerste aanvraag bevat de submission
                    'requests': requests  # Alle aanvragen voor deze submission
                })
            return grouped_requests
        
        # Haal de goedkeuringsgroepen op waar de gebruiker lid van is
        user_groups = user.approval_groups.all()
        
        # Voor pending tab: haal de aanvragen op waar de gebruiker nog op kan stemmen
        # 1. Het verzoek is nog in behandeling (status = PENDING)
        # 2. De gebruiker is niet de aanvrager
        # 3. De gebruiker is lid van minstens één groep die nog moet goedkeuren
        pending = ApprovalRequest.objects.filter(
            status='PENDING'
        ).exclude(
            requester=user
        ).filter(
            group_approvals__status='PENDING',
            group_approvals__group__in=user_groups
        ).select_related(
            'submission', 'requester'
        ).prefetch_related(
            'group_approvals', 'required_groups'
        ).distinct()
        
        # Voeg informatie toe aan elk verzoek over eerdere afwijzingen en welke groepen nog moeten goedkeuren
        for request in pending:
            # Controleer of er eerdere afgewezen verzoeken zijn
            request.has_previous_rejections = ApprovalRequest.objects.filter(
                submission=request.submission,
                status='REJECTED',
                created_at__lt=request.created_at
            ).exists()
            
            # Vind de groepen van deze gebruiker die nog moeten goedkeuren
            request.user_pending_groups = list(
                request.group_approvals.filter(
                    status='PENDING', 
                    group__in=user_groups
                ).select_related('group').values_list('group__name', flat=True)
            )
            
            # Voortgang bepalen
            total_required_groups = request.required_groups.count()
            approved_groups = request.group_approvals.filter(status='APPROVED').count()
            
            # Gebruik de status van GroupApproval objecten in plaats van een aangepaste berekening
            # Deze statussen zijn al correct ingesteld met inachtneming van de aanvrager
            request.approval_progress = 0
            if total_required_groups > 0:
                request.approval_progress = int((approved_groups / total_required_groups) * 100)
        
        # Sorteer op prioriteit: eerst verzoeken met eerdere afwijzingen, dan op aanvraagdatum (nieuwste eerst)
        return sorted(pending, key=lambda x: (-x.has_previous_rejections, -x.created_at.timestamp()))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Huidige tab (pending of reviewed)
        context['current_tab'] = self.request.GET.get('tab', 'pending')
        
        # Aantal openstaande verzoeken die deze gebruiker kan beoordelen
        user = self.request.user
        user_groups = user.approval_groups.all()
        
        context['pending_count'] = ApprovalRequest.objects.filter(
            status='PENDING'
        ).exclude(
            requester=user
        ).filter(
            group_approvals__status='PENDING',
            group_approvals__group__in=user_groups
        ).distinct().count()
        
        return context

class ApprovalRequestDetailView(ApprovalFeatureRequiredMixin, LoginRequiredMixin, DetailView):
    """Detailed view of a specific approval request"""
    model = ApprovalRequest
    template_name = 'approvals/request_detail.html'
    context_object_name = 'request'

    def get_queryset(self):
        qs = super().get_queryset()
        # Sta zowel beoordelaars als aanvragers toe
        if self.request.user.has_perm('approvals.can_review_submissions'):
            return qs
        return qs.filter(requester=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from instruments.views import process_gui_data, render_to_string
        
        # Generate all version previews first
        version_previews = {}
        historical_requests = self.object.submission.approval_requests.all()
        for request in historical_requests:
            if request.version:
                version = request.version
                preview_data = process_gui_data(
                    table_data=[[s['initials'], s['lastname'], s['party']] for s in version.submitters_data],
                    instrument=version.instrument,
                    subject=version.subject,
                    date_str=str(version.date),
                    considerations=version.considerations,
                    requests=version.requests
                )
                # Convert request.pk to string to match template behavior
                version_previews[str(request.pk)] = render_to_string("instruments/previews/template.txt", preview_data)
        
        # Add version previews to context
        context['version_previews'] = version_previews
        
        # Generate main preview for current request
        if self.object.version:
            version = self.object.version
            preview_data = process_gui_data(
                table_data=[[s['initials'], s['lastname'], s['party']] for s in version.submitters_data],
                instrument=version.instrument,
                subject=version.subject,
                date_str=str(version.date),
                considerations=version.considerations,
                requests=version.requests
            )
            context['preview'] = render_to_string("instruments/previews/template.txt", preview_data)
        else:
            # Fallback to current submission data if no version exists
            submission = self.object.submission
            table_data = [[s.initials, s.lastname, s.party] for s in submission.submitters.all()]
            preview_data = process_gui_data(
                table_data=table_data,
                instrument=submission.instrument,
                subject=submission.subject,
                date_str=str(submission.date),
                considerations=submission.considerations,
                requests=submission.requests
            )
            context['preview'] = render_to_string("instruments/previews/template.txt", preview_data)
        
        # Add approval logs to context, ordered by timestamp
        context['logs'] = self.object.logs.all().order_by('-timestamp')
        
        return context

class CreateApprovalRequestView(ApprovalFeatureRequiredMixin, LoginRequiredMixin, CreateView):
    """View for creating a new approval request"""
    model = ApprovalRequest
    form_class = ApprovalRequestForm
    template_name = 'approvals/create_request.html'

    def get_success_url(self):
        return reverse('instrument_submission_detail', kwargs={'pk': self.object.submission.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submission = get_object_or_404(InstrumentSubmission, pk=self.kwargs['submission_pk'])
        context['submission'] = submission
        
        # Get preview data
        from instruments.views import process_gui_data, render_to_string
        table_data = [[s.initials, s.lastname, s.party] for s in submission.submitters.all()]
        preview_data = process_gui_data(
            table_data=table_data,
            instrument=submission.instrument,
            subject=submission.subject,
            date_str=str(submission.date),
            considerations=submission.considerations,
            requests=submission.requests
        )
        context['preview'] = render_to_string("instruments/previews/template.txt", preview_data)
        return context

    def form_valid(self, form):
        submission = get_object_or_404(InstrumentSubmission, pk=self.kwargs['submission_pk'])
        form.instance.submission = submission
        form.instance.requester = self.request.user
        form.instance.status = 'PENDING'

        # Create a version of the submission at this point in time
        from instruments.models import InstrumentVersion
        version = InstrumentVersion.create_from_submission(submission)
        form.instance.version = version
        
        response = super().form_valid(form)
        
        # Initialiseer de groepsgoedkeuringen
        self.object.initialize_group_approvals()
        
        # Create log entry for submission with the request_comment
        ApprovalLog.objects.create(
            approval=self.object,
            user=self.request.user,
            action='submitted',
            comment=form.cleaned_data.get('request_comment', '')
        )
        
        messages.success(self.request, 'Goedkeuringsverzoek is succesvol ingediend.')
        return response

class ApproveRequestView(ApprovalBaseMixin, View):
    """View for approving a request"""
    def post(self, request, *args, **kwargs):
        approval_request = get_object_or_404(ApprovalRequest, pk=kwargs['pk'])
        
        # Check if user can review this request
        if not approval_request.can_user_review(request.user):
            messages.error(request, 'Je kunt dit verzoek niet beoordelen.')
            return redirect('approvals:request_detail', pk=approval_request.pk)
            
        if approval_request.status != 'PENDING':
            messages.error(request, 'Dit verzoek kan niet meer worden beoordeeld.')
            return redirect('approvals:request_detail', pk=approval_request.pk)

        form = ReviewForm(request.POST)
        if form.is_valid():
            # Haal de groepsgoedkeuringen op waar de gebruiker lid van is
            user_group_approvals = approval_request.group_approvals.filter(
                group__members=request.user
            )
            
            if not user_group_approvals.exists():
                messages.error(request, 'Je bent geen lid van een vereiste goedkeuringsgroep.')
                return redirect('approvals:request_detail', pk=approval_request.pk)
            
            # Controleer of de gebruiker de aanvrager is
            if approval_request.requester == request.user:
                messages.error(request, 'Je kunt niet stemmen op je eigen aanvraag.')
                return redirect('approvals:request_detail', pk=approval_request.pk)
            
            approval_count = 0
            for group_approval in user_group_approvals:
                # Gebruik de nieuwe can_user_vote methode om te controleren of de gebruiker mag stemmen
                if not group_approval.can_user_vote(request.user):
                    continue
                
                # Voeg de gebruiker toe aan de lijst van leden die hebben goedgekeurd
                group_approval.approved_members.add(request.user)
                
                # Update de laatste beoordelaar en opmerkingen informatie
                group_approval.reviewer = request.user
                group_approval.review_comment = form.cleaned_data['comment']
                group_approval.reviewed_at = timezone.now()
                group_approval.save()
                
                # Update de status van de groepsgoedkeuring
                group_approval.update_status()
                
                # Creëer log entry voor de goedkeuring
                ApprovalLog.objects.create(
                    approval=approval_request,
                    user=request.user,
                    action=f'approved_as_member_of_{group_approval.group.name}',
                    comment=form.cleaned_data['comment']
                )
                
                approval_count += 1
            
            if approval_count == 0:
                messages.info(request, 'Je kunt dit verzoek niet goedkeuren. Mogelijk ben je de aanvrager of heb je al gestemd.')
                return redirect('approvals:request_detail', pk=approval_request.pk)
            
            # Update de algemene status van het verzoek
            approval_request.update_status_based_on_group_approvals()
            
            if approval_request.status == 'APPROVED':
                messages.success(request, 'Het verzoek is volledig goedgekeurd.')
            else:
                messages.success(request, f'Je goedkeuring is opgeslagen. Er zijn nog andere goedkeuringen nodig.')
                
            return redirect('approvals:request_detail', pk=approval_request.pk)
        
        messages.error(request, 'Er is een fout opgetreden bij het verwerken van het formulier.')
        return redirect('approvals:request_detail', pk=approval_request.pk)

class RejectRequestView(ApprovalBaseMixin, View):
    """View for rejecting a request"""
    def post(self, request, *args, **kwargs):
        approval_request = get_object_or_404(ApprovalRequest, pk=kwargs['pk'])
        
        # Check if user can review this request
        if not approval_request.can_user_review(request.user):
            messages.error(request, 'Je kunt dit verzoek niet beoordelen.')
            return redirect('approvals:request_detail', pk=approval_request.pk)
            
        if approval_request.status != 'PENDING':
            messages.error(request, 'Dit verzoek kan niet meer worden beoordeeld.')
            return redirect('approvals:request_detail', pk=approval_request.pk)

        form = ReviewForm(request.POST)
        if form.is_valid():
            if not form.cleaned_data['comment']:
                messages.error(request, 'Een toelichting is verplicht bij het afwijzen van een verzoek.')
                return redirect('approvals:request_detail', pk=approval_request.pk)

            # Haal de groepsgoedkeuringen op waar de gebruiker lid van is
            user_group_approvals = approval_request.group_approvals.filter(
                group__members=request.user
            )
            
            if not user_group_approvals.exists():
                messages.error(request, 'Je bent geen lid van een vereiste goedkeuringsgroep.')
                return redirect('approvals:request_detail', pk=approval_request.pk)
            
            # Controleer of de gebruiker de aanvrager is
            if approval_request.requester == request.user:
                messages.error(request, 'Je kunt niet stemmen op je eigen aanvraag.')
                return redirect('approvals:request_detail', pk=approval_request.pk)
                
            rejection_count = 0
            for group_approval in user_group_approvals:
                # Gebruik de nieuwe can_user_vote methode om te controleren of de gebruiker mag stemmen
                if not group_approval.can_user_vote(request.user):
                    continue
                
                # Voeg de gebruiker toe aan de lijst van leden die hebben afgewezen
                group_approval.rejected_members.add(request.user)
                
                # Update de laatste beoordelaar en opmerkingen informatie
                group_approval.reviewer = request.user
                group_approval.review_comment = form.cleaned_data['comment']
                group_approval.reviewed_at = timezone.now()
                
                # Stel de groepsgoedkeuring direct in op afgewezen
                group_approval.status = 'REJECTED'
                group_approval.save()
                
                # Creëer log entry voor de afwijzing
                ApprovalLog.objects.create(
                    approval=approval_request,
                    user=request.user,
                    action=f'rejected_as_member_of_{group_approval.group.name}',
                    comment=form.cleaned_data['comment']
                )
                
                rejection_count += 1
                
                # Eén afwijzing is genoeg, dus we stoppen na de eerste groep
                break
            
            if rejection_count == 0:
                messages.info(request, 'Je kunt dit verzoek niet afwijzen. Mogelijk ben je de aanvrager of heb je al gestemd.')
                return redirect('approvals:request_detail', pk=approval_request.pk)
            
            # Eén afwijzing is genoeg om het hele verzoek af te wijzen
            approval_request.update_status_based_on_group_approvals()
            
            messages.success(request, f'Het verzoek is afgewezen op basis van jouw beoordeling.')
            return redirect('approvals:request_detail', pk=approval_request.pk)
        
        messages.error(request, 'Er is een fout opgetreden bij het verwerken van het formulier.')
        return redirect('approvals:request_detail', pk=approval_request.pk)

class CompareVersionsView(ApprovalFeatureRequiredMixin, LoginRequiredMixin, View):
    """View voor het vergelijken van twee versies van een instrument"""
    template_name = 'approvals/compare_versions.html'

    def get(self, request):
        version_ids = request.GET.getlist('versions')
        if len(version_ids) != 2:
            messages.error(request, 'Selecteer precies twee versies om te vergelijken.')
            return redirect(request.META.get('HTTP_REFERER', 'approvals:dashboard'))

        try:
            # Haal de approval requests op met de versies
            requests = list(ApprovalRequest.objects.filter(pk__in=version_ids).order_by('created_at'))
            
            if len(requests) != 2:
                messages.error(request, 'Een of beide versies konden niet worden gevonden.')
                return redirect(request.META.get('HTTP_REFERER', 'approvals:dashboard'))

            # Zorg ervoor dat requests[0] de oudste is en requests[1] de nieuwste
            version1_request = requests[0]  # Oudste
            version2_request = requests[1]  # Nieuwste

            # Controleer of de gebruiker toegang heeft tot deze requests
            if not (request.user.has_perm('approvals.can_review_submissions') or 
                   request.user == version1_request.requester or 
                   request.user == version2_request.requester):
                messages.error(request, 'Je hebt geen toegang tot deze versies.')
                return redirect('approvals:dashboard')

            # Zorg ervoor dat beide requests versies hebben
            if not (version1_request.version and version2_request.version):
                messages.error(request, 'Een of beide geselecteerde verzoeken heeft geen versie informatie.')
                return redirect(request.META.get('HTTP_REFERER', 'approvals:dashboard'))

            # Genereer previews voor beide versies
            from instruments.views import process_gui_data, render_to_string
            
            version1 = version1_request.version  # Oudste versie
            version2 = version2_request.version  # Nieuwste versie

            preview1_data = process_gui_data(
                table_data=[[s['initials'], s['lastname'], s['party']] for s in version1.submitters_data],
                instrument=version1.instrument,
                subject=version1.subject,
                date_str=str(version1.date),
                considerations=version1.considerations,
                requests=version1.requests
            )

            preview2_data = process_gui_data(
                table_data=[[s['initials'], s['lastname'], s['party']] for s in version2.submitters_data],
                instrument=version2.instrument,
                subject=version2.subject,
                date_str=str(version2.date),
                considerations=version2.considerations,
                requests=version2.requests
            )

            context = {
                'version1': {
                    'request': version1_request,
                    'preview': render_to_string("instruments/previews/template.txt", preview1_data)
                },
                'version2': {
                    'request': version2_request,
                    'preview': render_to_string("instruments/previews/template.txt", preview2_data)
                },
                'submission': version1_request.submission  # Voor broodkruimelpad
            }

            return render(request, self.template_name, context)

        except ValueError:
            messages.error(request, 'Een of beide versies konden niet worden gevonden.')
            return redirect(request.META.get('HTTP_REFERER', 'approvals:dashboard'))