from django.contrib import admin
from .models import ApprovalRequest, ApprovalLog, ApprovalGroup, GroupApproval

class ApprovalLogInline(admin.TabularInline):
    model = ApprovalLog
    extra = 0
    readonly_fields = ['timestamp', 'user', 'action', 'comment']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

class GroupApprovalInline(admin.TabularInline):
    model = GroupApproval
    extra = 0
    readonly_fields = ['reviewed_at']
    raw_id_fields = ['reviewer']

@admin.register(ApprovalGroup)
class ApprovalGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'get_member_count')
    search_fields = ['name']
    filter_horizontal = ('members',)
    
    def get_member_count(self, obj):
        return obj.members.count()
    get_member_count.short_description = 'Aantal leden'

@admin.register(GroupApproval)
class GroupApprovalAdmin(admin.ModelAdmin):
    list_display = ('approval_request', 'group', 'status', 'reviewer', 'reviewed_at')
    list_filter = ('status', 'group', 'reviewed_at')
    search_fields = ('approval_request__id', 'group__name', 'reviewer__email')
    raw_id_fields = ['approval_request', 'reviewer']

@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ['submission', 'requester', 'status', 'created_at', 'reviewer', 'reviewed_at']
    list_filter = ['status', 'created_at', 'reviewed_at', 'required_groups']
    search_fields = ['submission__subject', 'requester__email', 'reviewer__email', 'request_comment', 'review_comment']
    readonly_fields = ['created_at', 'reviewed_at']
    raw_id_fields = ['submission', 'requester', 'reviewer']
    filter_horizontal = ['required_groups']
    date_hierarchy = 'created_at'
    inlines = [GroupApprovalInline, ApprovalLogInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('submission', 'requester', 'reviewer')
    
    def has_add_permission(self, request):
        # Disable manual creation in admin - should be created through the application
        return False

@admin.register(ApprovalLog)
class ApprovalLogAdmin(admin.ModelAdmin):
    list_display = ['approval', 'user', 'action', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['approval__submission__subject', 'user__email']
    readonly_fields = ['timestamp']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('approval', 'user')