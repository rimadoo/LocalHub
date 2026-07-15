LocalHub is a digital community platform designed to connect people looking for services with local workers and creators in their neighborhood (like Uttara, Dhaka). Built using Python Django, Bootstrap 5, and Vanilla JavaScript, it brings structure, trust, and secure digital payments to local everyday services.

The Three Pillars of LocalHub
The system divides community needs into three main categories:

Daily Labor Hub (Physical Tasks): Allows clients (Seekers) to post local manual jobs (like plumbing, electrical work, or moving help). Registered and verified workers can view these posts and quickly find work nearby.

Online Tech Marketplace (Digital Services): A dedicated section for freelance tech tasks (like web setup, graphic design, or video editing). Service providers can submit bids, pitch their timelines, and set their price points.

Creative Shop (Artistic Marketplace): A storefront gallery where local artisans can display and sell handmade items (like woodwork or paintings). To ensure quality control, new items are hidden until an Admin manually reviews and approves them.

How It Works
1. User Accounts & Digital Wallets
When a user registers, the system sets them up as either a Seeker (client) or a Provider (worker/artist).

Every account automatically gets a built-in Digital Wallet. This wallet handles balance tracking, holds secure payments, and records all income and expenses.

2. Job Lifecycle & Safe Escrow Logic
Posting a Job: When a Seeker creates a job post, Django Signals run automatically in the background. It instantly sends an in-app notification and prints a simulated SMS log to alert all local workers about the new opportunity.

The Handshake: Providers browse active listings and submit an application with their bid message.

Secure Escrow: When the Seeker picks a worker, the system immediately checks the Seeker's wallet and locks the required budget inside the system (Escrow). The job status updates to Assigned. This protects the worker by proving the client has the funds ready.

Safe Release: Once the job is finished, the Seeker marks it as complete. Using a secure transaction.atomic() block, the system automatically marks the job as Completed, transfers the locked funds directly into the worker's wallet, creates an immutable digital receipt, and alerts the worker.

3. Payment Gateway & Cart Checkout
Adding Money: LocalHub integrates the SSLCommerz Payment Gateway in sandbox mode. This allows users to safely deposit funds into their digital wallets using regular local payment methods like bKash, Nagad, or cards.

Smart Shopping Cart: In the Creative Shop, users can add items to a shopping cart managed right inside the browser's LocalStorage for a fast experience. When checking out, this data is sent to the Django backend to either deduct money from the user's wallet or seamlessly switch the order to Cash on Delivery (COD) if the wallet balance is too low.

Tech Stack & Security
Backend Framework: Python Django (Following clean Model-View-Template architecture)

Frontend Design: Bootstrap 5 (Responsive UI), Vanilla JavaScript & AJAX, HTML5, CSS3

Database Engine: SQLite (Organized using clean, normalized relational tables)

Security Practices: Secure password hashing (Django default PBKDF2), role-based view controls, Cross-Site Request Forgery (CSRF) protection tokens, and database transaction protection.
