import uuid
import random
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    USER_TYPES = (('seeker', 'Seeker'), ('provider', 'Provider'))
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=USER_TYPES, default='seeker')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # --- NEW SAFETY VALIDATIONS FIELDS ---
    is_phone_verified = models.BooleanField(default=False)
    nid_number = models.CharField(max_length=17, blank=True, null=True)
    is_identity_verified = models.BooleanField(default=False)
    trust_score = models.IntegerField(default=100) # Deducts if they violate safety rules

    def __str__(self):
        return f"{self.user.username} - {self.role} (Verified: {self.is_identity_verified})"

class Task(models.Model):
    CATEGORY_CHOICES = (('labor', 'Daily Labor'), ('tech', 'Online Tech'))
    STATUS_CHOICES = (
        ('open', 'Open'), 
        ('assigned', 'Assigned'), 
        ('in_progress', 'In Progress'), 
        ('completed', 'Completed')
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100, default="Uttara, Dhaka")
    budget = models.DecimalField(max_digits=10, decimal_places=2)  # Standard Single Worker Budget
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')

    # --- SAFETY SECURE DYNAMIC PIN ---
    secure_handshake_pin = models.CharField(max_length=4, blank=True, null=True)

    def generate_pin(self):
        """ Generates a random 4-digit code when a single provider is hired """
        self.secure_handshake_pin = str(random.randint(1000, 9999))
        self.save()

    def __str__(self):
        return self.title
class CreativeItem(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(default="No description provided.")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # CHANGE THIS LINE: from image_url to image
    image = models.ImageField(upload_to='creative_gallery/', blank=True, null=True)
    
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creative_products')
    is_approved = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.title} - {'Approved' if self.is_approved else 'Pending'}"
# --- 4. Transaction (Dependencies: Task, User) ---
# This must come AFTER Task.
class Transaction(models.Model):
    TRAN_TYPES = (
        ('payment', 'Task Payment'),
        ('withdraw', 'Withdrawal'),
        ('deposit', 'Deposit'),
    )

    transaction_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    # Changed to ForeignKey and allowed null for withdrawals
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Allowed null because a withdrawal only involves one user
    seeker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_made', null=True, blank=True)
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earnings_received', null=True, blank=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    # Added type to distinguish withdrawals in your Activity Log
    type = models.CharField(max_length=10, choices=TRAN_TYPES, default='payment')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        short_id = str(self.transaction_id)[:8]
        return f"{self.get_type_display()} - {short_id} | ৳{self.amount}"
    

class TaskApplication(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.applicant.username} applied for {self.task.title}"    
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"
    
class TaskMessage(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender.username} regarding {self.task.title}"

    
    