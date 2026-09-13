# Library Management System

A role-based library management application featuring open catalog search for guests alongside reader management, circulation tracking, and analytics for librarians.

---

## Features

### Role-Based Access
* **Guest (Public):** Read-only access restricted strictly to the **Available Books** catalog.
* **Librarian (Admin):** Full administrative privileges across all modules:
  * Full CRUD on books (Add, Edit, Delete, View all titles).
  * Reader registration and account management.
  * Borrow and return circulation control.
  * System analytics dashboard.

### Core Functionality
* **Public Catalog Search:** Quick lookup of currently available titles for guests.
* **Reader Management:** Register new library members and update profiles.
* **Circulation Control:** Issue book loans, process returns, and monitor overdue deadlines.
* **Analytics & Reports:**
  * **Popular Titles:** Track the most borrowed books over time.
  * **Overdue Tracking:** Count and monitor unreturned books past their due date.
  * **Borrowing Trends:** Measure loan activity across customizable date ranges.

---

## Access Control Matrix

| Module / Action | Guest Role | Librarian Role |
| :--- | :---: | :---: |
| **Available Books Catalog** | Read-Only | Full CRUD |
| **Borrowed / Total Books Inventory** | Hidden | Full Access |
| **Reader Registration & Profiles** | Hidden | Full CRUD |
| **Loan & Return Processing** | Hidden | Full CRUD |
| **System Analytics** | Hidden | Full Access |

---

## Prerequisites

* Python 3.10+
* MySQL Server

---
