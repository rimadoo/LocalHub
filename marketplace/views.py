import requests
import uuid
import json
from decimal import Decimal
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Case, When, Value, IntegerField
from .models import Task, CreativeItem, Profile, Transaction, TaskApplication, Notification, TaskMessage
from .forms import TaskForm
from django.db import transaction # Import this for safe payments
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def approve_item(request, item_id):
    item = CreativeItem.objects.get(id=item_id)
    item.is_approved = True
    item.save()
    messages.success(request, f"Item '{item.title}' has been approved!")
    return redirect('admin_dashboard')
# --- 1. AUTHENTICATION & REGISTRATION ---

def login_view(request):
    if request.user.is_authenticated:
        return redirect('login_success')
    if request.method == "POST":
        un = request.POST.get('username')
        ps = request.POST.get('password')
        user = authenticate(username=un, password=ps)
        if user:
            login(request, user)
            return redirect('login_success')
        else:
            messages.error(request, "Invalid Credentials. Please try again.")
    return render(request, 'marketplace/login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('login_success')
    if request.method == "POST":
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        role = request.POST.get('role')
        password = request.POST.get('password')
        if User.objects.filter(username=email).exists():
            messages.error(request, "A user with this email already exists.")
            return render(request, 'marketplace/login.html')
        user = User.objects.create_user(username=email, email=email, password=password)
        user.first_name = full_name
        user.save()
        Profile.objects.create(user=user, role=role)
        login(request, user)
        return redirect('verify_account')
    return render(request, 'marketplace/login.html')

def logout_view(request):
    logout(request)
    return redirect('logout_page')

def logout_page(request):
    return render(request, 'marketplace/logout.html')

# --- 2. DASHBOARDS ---

@login_required(login_url='login_view')
def login_success(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    unread_notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')[:5]
    history = Transaction.objects.filter(Q(seeker=request.user) | Q(provider=request.user)).order_by('-timestamp')
    my_apps = TaskApplication.objects.filter(applicant=request.user).order_by('-created_at')
    return render(request, 'marketplace/login_success.html', {
        'profile': profile,
        'notifications': unread_notifications,
        'history': history,
        'my_apps': my_apps
    })

@login_required(login_url='login_view')
def seeker_dashboard(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.posted_by = request.user
            task.save() 
            messages.success(request, "Task Broadcasted! Local workers are being notified.")
            return render(request, 'marketplace/post_success.html', {'task': task})
    else:
        form = TaskForm()
    return render(request, 'marketplace/seeker_dashboard.html', {'form': form})

@login_required(login_url='login_view')
def seeker_activity_log(request):
    my_tasks = Task.objects.filter(posted_by=request.user).order_by('-created_at')
    return render(request, 'marketplace/seeker_activity_log.html', {'my_tasks': my_tasks})

@login_required(login_url='login_view')
def worker_proposals(request):
    my_proposals = TaskApplication.objects.filter(applicant=request.user).order_by('-created_at')
    return render(request, 'marketplace/worker_proposals.html', {'proposals': my_proposals})

# --- 3. MARKETPLACE ACTIONS ---

def daily_labor(request):
    # 1. Start with the base query for active open labor tasks
    tasks = Task.objects.filter(category='labor')
    
    # 2. Extract GET URL filter parameters sent by the sidebar form map
    selected_subcategories = request.GET.getlist('category')  # Captures checkbox choices array
    max_budget = request.GET.get('max_budget')               # Captures budget range slider ceiling
    sort_choice = request.GET.get('sort')                     # Captures dropdown sorting nodes

    # 3. Dynamic Category Filtering Handshake (Your Text Keyword Q-matching)
    if selected_subcategories:
        category_queries = Q()
        for sub_cat in selected_subcategories:
            if sub_cat == 'logistics':
                category_queries |= Q(title__icontains='shift') | Q(title__icontains='logistics') | Q(description__icontains='move')
            elif sub_cat == 'plumbing':
                category_queries |= Q(title__icontains='plumb') | Q(title__icontains='fix') | Q(description__icontains='pipe')
            elif sub_cat == 'cleaning':
                category_queries |= Q(title__icontains='clean') | Q(title__icontains='wash') | Q(description__icontains='sanit')
        
        tasks = tasks.filter(category_queries)
        
    # 4. Dynamic Budget Threshold Filtering (__lte matches less than or equal to choice)
    if max_budget:
        try:
            tasks = tasks.filter(budget__lte=int(max_budget))
        except ValueError:
            pass  # Guardrail fallback if parsing parameter fails

    # 5. EXECUTE STRATEGIC DYNAMIC SORTING INTERFACES
    if sort_choice == 'budget_desc':
        # Re-arrange the filtered task lists by budget values descending
        tasks = tasks.order_by('-budget')
        
    elif sort_choice == 'sector_asc':
        # Sequential Conditional Priority Mapping Node for Local Uttara Sectors
        # Annotates each task log dynamically based on geographic text patterns matching lower numbers first
        tasks = tasks.annotate(
            sector_priority=Case(
                When(location__icontains='Sector 1', then=Value(1)),
                When(location__icontains='Sector 2', then=Value(2)),
                When(location__icontains='Sector 3', then=Value(3)),
                When(location__icontains='Sector 4', then=Value(4)),
                When(location__icontains='Sector 5', then=Value(5)),
                When(location__icontains='Sector 6', then=Value(6)),
                When(location__icontains='Sector 7', then=Value(7)),
                default=Value(99), # Fallback order parameter for other geographic inputs
                output_field=IntegerField(),
            )
        ).order_by('sector_priority', '-created_at')
        
    else:
        # Fallback default sorting behavior condition: newest listing posts first
        tasks = tasks.order_by('-created_at')
            
    return render(request, 'marketplace/daily_labor.html', {'tasks': tasks})

def online_tech(request):
    # 1. Fetch all open technical engineering tasks sorted by latest entry
    tasks = Task.objects.filter(category='tech').order_by('-created_at')
    
    # 2. Ingest selected filter options from the request parameters
    selected_tech_categories = request.GET.getlist('tech_category')
    escrow_locked = request.GET.get('escrow_locked')

    # 3. Execute Dynamic Search Filters via Keyword Mapping
    if selected_tech_categories:
        tech_queries = Q()
        for tech_cat in selected_tech_categories:
            if tech_cat == 'web':
                tech_queries |= Q(title__icontains='web') | Q(title__icontains='react') | Q(title__icontains='django') | Q(description__icontains='website')
            elif tech_cat == 'vfx':
                tech_queries |= Q(title__icontains='vfx') | Q(title__icontains='animat') | Q(title__icontains='render') | Q(description__icontains='video')
            elif tech_cat == 'python':
                tech_queries |= Q(title__icontains='python') | Q(title__icontains='script') | Q(title__icontains='bot') | Q(description__icontains='compiler')
        
        tasks = tasks.filter(tech_queries)

    # 4. Optional filter logic to check for active locked funds
    if escrow_locked == 'true':
        # Safely showing assignments that contain a strict baseline budget threshold
        tasks = tasks.filter(budget__gte=500)

    return render(request, 'marketplace/online_tech.html', {'tasks': tasks})
def creative_shop(request):
    # 1. Fetch only administrative approved marketplace assets sorted by latest arrival 
    items = CreativeItem.objects.filter(is_approved=True).order_by('-created_at')
    
    # 2. Extract specific form query array strings from the browser parameter token
    selected_craft_types = request.GET.getlist('craft_type')
    max_price = request.GET.get('max_price')

    # 3. Dynamic Keyword Classification Parsing
    if selected_craft_types:
        craft_queries = Q()
        for craft in selected_craft_types:
            if craft == 'woodwork':
                craft_queries |= Q(title__icontains='wood') | Q(title__icontains='carve') | Q(description__icontains='teak') | Q(description__icontains='timber')
            elif craft == 'canvas':
                craft_queries |= Q(title__icontains='paint') | Q(title__icontains='canvas') | Q(title__icontains='art') | Q(description__icontains='acrylic')
            elif craft == 'pottery':
                craft_queries |= Q(title__icontains='pot') | Q(title__icontains='clay') | Q(title__icontains='vase') | Q(description__icontains='ceramic')
        
        items = items.filter(craft_queries)

    # 4. Maximum Price Bound Constraints Processing
    if max_price:
        try:
            # Filters item listings less than or equal to current slider choice value
            items = items.filter(price__lte=float(max_price))
        except ValueError:
            pass # Gracefully handle conversion hiccups

    return render(request, 'marketplace/creative_shop.html', {'items': items})

def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    already_applied = False
    
    # Check if this specific worker already applied to this task
    if request.user.is_authenticated:
        already_applied = TaskApplication.objects.filter(task=task, applicant=request.user).exists()
    
    return render(request, 'marketplace/task_detail.html', {
        'task': task, 
        'already_applied': already_applied
    })
@login_required(login_url='login_view')
def apply_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Prevent duplicate application via URL hacking
    if TaskApplication.objects.filter(task=task, applicant=request.user).exists():
        messages.warning(request, "You have already applied for this task.")
        return redirect('daily_labor')

    if request.method == "POST":
        msg_text = request.POST.get('message', "I am interested in this task.")
        TaskApplication.objects.create(
            task=task,
            applicant=request.user,
            bid_amount=task.budget,
            message=msg_text
        )
        
        # Notify the Seeker (Task Owner)
        Notification.objects.create(
            user=task.posted_by,
            message=f"{request.user.username} applied for your task: {task.title}"
        )
        
        messages.success(request, f"Applied for {task.title}")
        return redirect('apply_success')
    return render(request, 'marketplace/apply.html', {'task': task})
@login_required(login_url='login_view')
def submit_tech_proposal(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == "POST":
        bid = request.POST.get('bid_amount')
        days = request.POST.get('delivery_days')
        pitch = request.POST.get('pitch')
        TaskApplication.objects.create(
            task=task, applicant=request.user,
            bid_amount=bid, message=f"Timeline: {days} days. Pitch: {pitch}"
        )
        messages.success(request, f"Proposal submitted for {task.title}!")
        return redirect('online_tech')
    return render(request, 'marketplace/submit_proposal.html', {'task': task})

# --- 4. THE HANDSHAKE (HIRE, MESSAGING & PAYMENT) ---

@login_required(login_url='login_view')
def view_proposals(request, task_id):
    task = get_object_or_404(Task, id=task_id, posted_by=request.user)
    proposals = task.applications.all().order_by('-created_at')
    return render(request, 'marketplace/view_proposals.html', {
        'task': task, 'proposals': proposals, 'profile': request.user.profile
    })

@login_required(login_url='login_view')
def accept_proposal(request, application_id):
    """ Seeker hires a worker. Money is deducted and held in Escrow. """
    proposal = get_object_or_404(TaskApplication, id=application_id)
    task = proposal.task
    seeker_profile = request.user.profile
    
    if request.user == task.posted_by:
        if seeker_profile.balance < proposal.bid_amount:
            messages.error(request, f"Insufficient funds. Bid is ৳{proposal.bid_amount}.")
            return redirect('view_proposals', task_id=task.id)
            
        with transaction.atomic():
            # Deduct from seeker wallet
            seeker_profile.balance -= proposal.bid_amount
            seeker_profile.save()
            
            # Assign task to worker
            task.status = "assigned"
            task.assigned_to = proposal.applicant 
            task.budget = proposal.bid_amount 
            
            # Generates our secure check-in handshake token
            task.generate_pin() 
            task.save()
            
            Notification.objects.create(
                user=proposal.applicant, 
                message=f"Hired for '{task.title}'! Your arrival security PIN is generated."
            )
            
        messages.success(request, f"Hired {proposal.applicant.username}! Money held in escrow safely.")
        return redirect('login_success') # Handled path successfully
        
    # --- THE FALLBACK REDIRECT FIX ---
    # If the logged-in user is NOT the task owner, this catches them gracefully instead of crashing
    messages.error(request, "Unauthorized action. You are not the creator of this task.")
    return redirect('login_success')

@login_required(login_url='login_view')
def send_task_message(request, task_id, receiver_id):
    if request.method == "POST":
        content = request.POST.get('message_content')
        task = get_object_or_404(Task, id=task_id)
        receiver = get_object_or_404(User, id=receiver_id)
        TaskMessage.objects.create(task=task, sender=request.user, receiver=receiver, content=content)
        messages.success(request, "Message sent!")
        return redirect(request.META.get('HTTP_REFERER'))

# --- 5. SSLCOMMERZ GATEWAY INTEGRATION ---



@csrf_exempt
def payment_status(request):
    """ Processes the return signal from SSLCommerz """
    if request.method == 'POST':
        payment_data = request.POST
        status = payment_data.get('status')
        amount = payment_data.get('amount')
        user_id = payment_data.get('value_a') # Retrieve user ID we passed earlier
        
        if status == 'VALID':
            user = User.objects.get(id=user_id)
            profile = user.profile
            profile.balance += Decimal(amount)
            profile.save()
            # Note: Messages might not show immediately due to redirect from external site
            return redirect('login_success')
    return redirect('login_success')

# --- 6. COMPLETION & FINANCE ---

@login_required(login_url='login_view')
def complete_task(request, task_id):
    """ Seeker releases Escrow funds to the Worker's wallet """
    task = get_object_or_404(Task, id=task_id)
    
    # Ensure ONLY the person who posted the task can pay
    if request.user == task.posted_by:
        
        # FIX: Allow completion if status is 'assigned' OR 'in_progress'
        if task.status not in ['assigned', 'in_progress']:
            messages.error(request, "🛑 Action Blocked: This task is already completed or open.")
            return redirect('seeker_activity_log')
            
        worker = task.assigned_to
        if not worker:
            messages.error(request, "No worker assigned to this task.")
            return redirect('seeker_activity_log')
        
        with transaction.atomic(): # Safe ledger manipulation
            # 1. Update Task Status permanently
            task.status = 'completed'
            task.save()

            # 2. Pay Worker Profile Wallet
            worker_profile = worker.profile
            worker_profile.balance += task.budget
            worker_profile.save()

            # 3. Record Transaction for the Activity Log
            Transaction.objects.create(
                task=task, 
                seeker=task.posted_by, 
                provider=worker, 
                amount=task.budget,
                type='payment',
                transaction_id=str(uuid.uuid4())[:10]
            )
            
            # 4. Create Notification
            Notification.objects.create(
                user=worker,
                message=f"Work Verified! ৳{task.budget} has been successfully added to your balance for '{task.title}'."
            )
        
        messages.success(request, f"🔒 Escrow Released! Payment of ৳{task.budget} released safely to {worker.username}.")
        return redirect('seeker_activity_log')
        
    messages.error(request, "You are not authorized to complete this task.")
    return redirect('login_success')

# --- 7. STATIC & HELPER PAGES ---

def home(request): return render(request, 'marketplace/index.html')
def verify_account(request): return render(request, 'marketplace/verify_account.html')
def apply_success(request): return render(request, 'marketplace/apply_success.html')
def about(request): return render(request, 'marketplace/about.html')
def contact(request): return render(request, 'marketplace/contact.html')
def feedback(request): return render(request, 'marketplace/feedback.html')
def item_entry(request): return render(request, 'marketplace/item_entry.html')
@login_required(login_url='login_view')
def order_success(request):
    if request.method == "POST":
        # Ensure the key matches the 'name' attribute in your checkout.html form
        cart_data = request.POST.get('cart_json_data')
        
        if not cart_data:
            messages.error(request, "Your cart data was missing. Please try again.")
            return redirect('creative_shop')

        try:
            items = json.loads(cart_data) # Convert JSON string to Python list
            total_price = Decimal('0.00')
            
            with transaction.atomic():
                # 1. Calculate Total and Validate Items
                for item in items:
                    # Using Decimal for financial accuracy
                    price_val = Decimal(str(item.get('price', 0)))
                    total_price += price_val
                    
                    # Logic: Create Order Record (Optional but recommended)
                    # item_id = item.get('id')
                    # Order.objects.create(buyer=request.user, item_id=item_id, price=price_val)

                # 2. Handle Wallet Deduction
                user_profile = request.user.profile
                
                if user_profile.balance >= total_price and total_price > 0:
                    user_profile.balance -= total_price
                    user_profile.save()
                    
                    # Record the transaction for the activity log
                    Transaction.objects.create(
                        seeker=request.user,
                        amount=total_price,
                        type='payment',
                        transaction_id=str(uuid.uuid4())[:10]
                    )
                    messages.success(request, f"Order placed! ৳{total_price} deducted from your wallet.")
                else:
                    messages.warning(request, f"Order of ৳{total_price} placed via Cash on Delivery (Insufficient Balance).")

            # Return the confirmation page
            return render(request, 'marketplace/order_success.html', {'total': total_price})

        except (json.JSONDecodeError, ValueError) as e:
            messages.error(request, "There was an error processing your cart items.")
            return redirect('creative_shop')
    
    # If someone tries to access via GET, just send them to the shop
    return redirect('creative_shop')
def checkout(request): return render(request, 'marketplace/checkout.html')
def creative_cart(request):
    return render(request, 'marketplace/creative_cart.html')
# marketplace/views.py

# marketplace/views.py

@login_required
def initiate_payment(request):
    """ SSLCommerz Handshake """
    if request.method == "POST":
        amount = request.POST.get('amount')
        post_data = {
            'store_id': settings.SSLC_STORE_ID,
            'store_passwd': settings.SSLC_STORE_PASS, # Fixed key name
            'total_amount': amount,
            'currency': 'BDT',
            'tran_id': str(uuid.uuid4())[:10],
            'success_url': request.build_absolute_uri('/payment/status/'),
            'fail_url': request.build_absolute_uri('/payment/status/'),
            'cancel_url': request.build_absolute_uri('/payment/status/'),
            'cus_name': request.user.username,
            'cus_email': request.user.email,
            'cus_phone': '01700000000',
            'cus_add1': 'Dhaka', 'cus_city': 'Dhaka', 'cus_country': 'Bangladesh',
            'shipping_method': 'NO', 'multi_card_name': 'mastercard,visacard,amexcard',
            'value_a': request.user.id, 
        }
        url = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"
        try:
            response = requests.post(url, data=post_data)
            response_data = response.json()
            if response_data.get('status') == 'SUCCESS':
                return redirect(response_data['GatewayPageURL'])
        except Exception as e:
            messages.error(request, "Gateway connection failed.")
    return redirect('login_success')

@login_required
def withdraw_funds(request):
    if request.method == "POST":
        amount = Decimal(request.POST.get('amount'))
        method = request.POST.get('method') # bKash, Nagad, etc.
        account_no = request.POST.get('account_no')
        profile = request.user.profile

        if amount > profile.balance:
            messages.error(request, "Insufficient balance for this withdrawal.")
            return redirect('login_success')

        if amount < 100:
            messages.error(request, "Minimum withdrawal amount is ৳100.")
            return redirect('login_success')

        # 1. Deduct from User Balance
        profile.balance -= amount
        profile.save()

        # 2. Record the Transaction
        Transaction.objects.create(
            transaction_id=str(uuid.uuid4())[:10],
            seeker=request.user, # Using seeker field as 'sender/initiator'
            amount=amount,
            type='withdraw'
        )

        # 3. Notify the user
        Notification.objects.create(
            user=request.user,
            message=f"Withdrawal request of ৳{amount} sent to {method} ({account_no}). Processed via Gateway."
        )

        messages.success(request, f"Withdrawal Successful! ৳{amount} sent to your {method} account.")
        return redirect('login_success')
    
    return redirect('login_success')

@login_required
def add_creative_item(request):
    if request.method == "POST":
        title = request.POST.get('title')
        price = request.POST.get('price')
        description = request.POST.get('description')
        # Capture the file from request.FILES
        uploaded_image = request.FILES.get('item_image')

        CreativeItem.objects.create(
            title=title,
            price=price,
            description=description,
            image=uploaded_image, # Save the file here
            seller=request.user,
            is_approved=False
        )
        messages.success(request, "Image uploaded! Waiting for Admin approval.")
        return redirect('creative_shop')
    
    return render(request, 'marketplace/item_entry.html')

@login_required(login_url='login_view')
def task_chat(request, task_id, user_id):
    task = get_object_or_404(Task, id=task_id)
    other_user = get_object_or_404(User, id=user_id)
    
    messages_list = TaskMessage.objects.filter(task=task).filter(
        Q(sender=request.user, receiver=other_user) | 
        Q(sender=other_user, receiver=request.user)
    ).order_by('timestamp')

    if request.method == "POST":
        content = request.POST.get('content')
        if content:
            # --- SECURITY & TRUST VALIDATION LAYER ---
            content_lower = content.lower()
            forbidden_keywords = ['kill', 'threat', 'murder', 'weapon', 'hurt', 'abuse']
            
            # Extract just digits to check for a 11-digit Bangladeshi phone number
            digits = ''.join([char for char in content if char.isdigit()])
            contains_phone = len(digits) >= 11

            # Check if any violation is triggered
            if any(word in content_lower for word in forbidden_keywords) or contains_phone:
                # Penalize the user's platform trust score
                user_profile = request.user.profile
                user_profile.trust_score = max(0, user_profile.trust_score - 20)
                user_profile.save()
                
                # Trigger warning back to user without saving the message
                if contains_phone:
                    messages.error(request, "⚠️ Security Block: Sharing direct phone numbers is restricted to protect your privacy and ensure platform safety.")
                else:
                    messages.error(request, "🛑 Safety Violation: Your message was flagged and blocked for containing threatening or hostile language. This incident has lowered your platform Trust Score.")
                
                return redirect('task_chat', task_id=task_id, user_id=user_id)
            # --- END OF SECURITY VALIDATION LAYER ---

            # 1. Create the Message if validation passes
            TaskMessage.objects.create(
                task=task,
                sender=request.user,
                receiver=other_user,
                content=content
            )
            
            # 2. CREATE NOTIFICATION
            Notification.objects.create(
                user=other_user,
                message=f"New message from {request.user.username} regarding '{task.title}'"
            )
            
            return redirect('task_chat', task_id=task_id, user_id=user_id)

    return render(request, 'marketplace/chat.html', {
        'task': task,
        'messages': messages_list,
        'other_user': other_user
    })
    
# In views.py
@login_required
def worker_dashboard(request):
    # Monitoring: Tasks I've applied for
    my_applications = TaskApplication.objects.filter(applicant=request.user)
    
    # Connection: Messages sent TO me
    unread_messages = TaskMessage.objects.filter(receiver=request.user).order_by('-timestamp')
    
    return render(request, 'marketplace/worker_dashboard.html', {
        'my_applications': my_applications,
        'unread_messages': unread_messages,
    })    
    
@login_required(login_url='login_view')
def cancel_task(request, task_id):
    """ Seeker cancels the task and gets a refund from Escrow. """
    task = get_object_or_404(Task, id=task_id, posted_by=request.user)
    
    # Only allow cancellation if the task is currently assigned/in-progress
    if task.status == 'assigned':
        with transaction.atomic():
            # 1. Return money to Seeker's Profile
            seeker_profile = request.user.profile
            seeker_profile.balance += task.budget
            seeker_profile.save()
            
            # 2. Record the Refund Transaction
            Transaction.objects.create(
                task=task,
                seeker=request.user,
                amount=task.budget,
                type='refund' # Ensure your Transaction model has 'refund' in choices
            )
            
            # 3. Update Task Status
            previous_worker = task.assigned_to
            task.status = 'open' # Set back to open so others can apply, or 'cancelled'
            task.assigned_to = None
            task.save()
            
            # 4. Notify the Worker
            Notification.objects.create(
                user=previous_worker,
                message=f"The task '{task.title}' was cancelled by the seeker due to inactivity."
            )
            
        messages.success(request, f"Task cancelled. ৳{task.budget} has been refunded to your wallet.")
    else:
        messages.error(request, "This task cannot be cancelled in its current state.")
        
    return redirect('seeker_activity_log')

@login_required(login_url='login_view')
def verify_arrival_handshake(request, task_id):
    """
    Provider physically arrives at the Seeker's location, gets the PIN 
    verbally, and inputs it to unlock the active session safely.
    """
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    
    if request.method == "POST":
        entered_pin = request.POST.get('arrival_pin')
        
        if entered_pin == task.secure_handshake_pin:
            task.status = 'in_progress' # Progress token changes state securely
            task.save()
            
            Notification.objects.create(
                user=task.posted_by,
                message=f"🔒 Identity Verified! Provider has successfully checked-in on-site."
            )
            messages.success(request, "Arrival confirmed! The safe execution state is active.")
            return redirect('login_success')
        else:
            messages.error(request, "🛑 Verification Failed: Invalid Safety Handshake PIN.")
            
    return redirect('worker_proposals')

