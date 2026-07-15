from django.urls import path
from . import views

urlpatterns = [
    # --- 1. General & Landing Pages ---
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('feedback/', views.feedback, name='feedback'),

    # --- 2. Authentication Flow ---
    path('login/', views.login_view, name='login_view'),
    path('register/', views.register_view, name='register_view'),
    path('logout/', views.logout_view, name='logout_view'),
    path('logged-out/', views.logout_page, name='logout_page'),
    path('welcome/', views.login_success, name='login_success'),
    path('verify/', views.verify_account, name='verify_account'),

    # --- 3. Dashboards & Activity Logs ---
    path('seeker-dashboard/', views.seeker_dashboard, name='seeker_dashboard'),
    path('activity-log/', views.seeker_activity_log, name='browse_tasks'),
    path('my-activity/', views.seeker_activity_log, name='seeker_activity_log'),
    path('my-proposals/', views.worker_proposals, name='worker_proposals'),

    # --- 4. Task Categories & Shop ---
    path('daily-labor/', views.daily_labor, name='daily_labor'),
    path('online-tech/', views.online_tech, name='online_tech'),
    path('creative-shop/', views.creative_shop, name='creative_shop'),
    
    # FIXED: Changed 'add_creative_items' to 'add_creative_item' to match your template
    path('creative-shop/add/', views.add_creative_item, name='add_creative_item'),
    path('sell-craft/', views.item_entry, name='item_entry_view'),

    # --- 5. Application & Proposal Flow ---
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('apply-task/<int:task_id>/', views.apply_task, name='apply_task'),
    path('apply-success/', views.apply_success, name='apply_success'),
    path('submit-proposal/<int:task_id>/', views.submit_tech_proposal, name='submit_tech_proposal'),
    
    # --- 6. Hiring & Escrow (The Handshake) ---
    path('task/<int:task_id>/proposals/', views.view_proposals, name='view_proposals'),
    path('accept-proposal/<int:application_id>/', views.accept_proposal, name='accept_proposal'),
    path('complete-task/<int:task_id>/', views.complete_task, name='complete_task'),
    path('send-message/<int:task_id>/<int:receiver_id>/', views.send_task_message, name='send_task_message'),

    # --- 7. Transactions ---
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/', views.order_success, name='order_success'),
    path('payment/initiate/', views.initiate_payment, name='initiate_payment'),
    path('payment/status/', views.payment_status, name='payment_status'),
    path('wallet/withdraw/', views.withdraw_funds, name='withdraw_funds'),
    path('approve-item/<int:item_id>/', views.approve_item, name='approve_item'),
    path('cancel-task/<int:task_id>/', views.cancel_task, name='cancel_task'),
    path('creative-cart/', views.creative_cart, name='creative_cart'),
    path('task/<int:task_id>/verify-arrival/', views.verify_arrival_handshake, name='verify_arrival_handshake'),
]