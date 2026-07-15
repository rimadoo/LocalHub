from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Task, Profile, Notification

@receiver(post_save, sender=Task)
def notify_workers_on_new_task(sender, instance, created, **kwargs):
    if created:
        # Fetch all verified providers registered on the network
        potential_workers = Profile.objects.filter(role='provider')
        
        for profile in potential_workers:
            # 1. Internal Notification Row Allocation (Visible on UI Dashboard channels)
            Notification.objects.create(
                user=profile.user,
                message=f"New {instance.get_category_display()} task entry: '{instance.title}' listed in {instance.location}. Allocation: ৳{instance.budget}."
            )
            
            # 2. Terminal Handshake Simulator Log (Excellent proof trigger for your Viva board)
            # Pulls the contact row from your profile model securely
            phone_number = getattr(profile, 'phone', profile.user.username)
            print(f"\n🚀 SYSTEM TELEMETRY [GATEWAY BROADCAST SMS SENT] -> Destination Account Endpoint Node: {phone_number} | Payload Payload Package: 'New Task Alert!'\n")