# marketplace/admin.py
from django.contrib import admin
from django.db import transaction
import uuid
from .models import (
    Profile, 
    Task, 
    CreativeItem, 
    Transaction, 
    TaskApplication, 
    Notification, 
    TaskMessage
)

# --- 1. Basic Registrations (No extra customization) ---
admin.site.register(Transaction)
admin.site.register(TaskApplication)
admin.site.register(Notification)
admin.site.register(TaskMessage)


# --- 2. Custom Registrations (Professional Monitoring) ---

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Manage User Roles and Balances"""
    list_display = ('user', 'role', 'balance')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')
    list_editable = ('balance',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Monitor Labor and Tech Jobs with Sub-Admin Role Isolation"""
    list_display = ('title', 'category', 'status', 'budget', 'location', 'created_at')
    list_filter = ('category', 'status', 'created_at')
    search_fields = ('title', 'description', 'location')
    list_editable = ('status',)
    date_hierarchy = 'created_at' 
    list_per_page = 20
    
    # Register our advanced administrative action module
    actions = ['force_resolve_dispute']

    # ─── DATA ISOLATION ENGINE ───
    def get_queryset(self, request):
        """ Dynamically filters records based on the logged-in agent's group role """
        qs = super().get_queryset(request)
        
        # 1. Main Admin / Superuser has full clearance to see everything
        if request.user.is_superuser:
            return qs
            
        # 2. Labor Ops Agents can only view physical Daily Labor rows
        if request.user.groups.filter(name="Labor_Ops_Agent").exists():
            return qs.filter(category='labor')
            
        # 3. Tech Ops Agents can only view remote Online Tech jobs
        if request.user.groups.filter(name="Tech_Ops_Agent").exists():
            return qs.filter(category='tech')
            
        # 4. Safe Guard fallback - Unassigned staff see nothing
        return qs.none()

    # ─── SECURITY ENGINE ───
    def has_delete_permission(self, request, obj=None):
        """ Restricts row destruction. Only you (the Main Admin) can delete tasks from the DB """
        if request.user.is_superuser:
            return True
        return False # Removes delete checkboxes and action buttons for sub-admin agents

    # ─── DISPUTE OVERRIDE SYSTEM ───
    @admin.action(description="⚠️ Force Administrative Escrow Release (Dispute Resolution)")
    def force_resolve_dispute(self, request, queryset):
        """ System override to resolve user lockouts and release locked escrow funds safely """
        success_count = 0
        
        for task in queryset:
            # Only resolve tasks that are active and have an assigned worker
            if task.status in ['assigned', 'in_progress'] and task.assigned_to:
                with transaction.atomic():
                    # 1. Update project status state
                    task.status = 'completed'
                    task.save()
                    
                    # 2. Credit the assigned Worker's wallet profile directly
                    worker_profile = task.assigned_to.profile
                    worker_profile.balance += task.budget
                    worker_profile.save()
                    
                    # 3. Record a transparent financial ledger entry for audit history
                    Transaction.objects.create(
                        task=task,
                        seeker=task.posted_by,
                        provider=task.assigned_to,
                        amount=task.budget,
                        type='payment',
                        transaction_id=str(uuid.uuid4())[:10]
                    )
                    
                    # 4. Notify the worker
                    Notification.objects.create(
                        user=task.assigned_to,
                        message=f"Administrative Action: Escrow has been manually released by platform staff for '{task.title}'."
                    )
                    
                    success_count += 1
                    
        self.message_user(
            request, 
            f"Successfully resolved disputes for {success_count} tasks. Funds released cleanly to provider wallets."
        )


@admin.register(CreativeItem)
class CreativeItemAdmin(admin.ModelAdmin):
    """Monitor the Creative Shop Gallery"""
    list_display = ('title', 'seller', 'price', 'is_approved', 'created_at')
    list_editable = ('is_approved',)
    list_filter = ('is_approved', 'created_at')
    search_fields = ('title', 'seller__username')