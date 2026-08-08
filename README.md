# Trekking Management App

Flask + SQLite web app for managing treks, staff, and bookings — MAD I project

A simple administrative application to create and manage treks, staff members, and customer bookings. Suitable for small trekking operators, demoing CRUD, user flows and lightweight persistence with SQLite.

## Features
- Create, read, update, delete (CRUD) treks (name, location, date, difficulty, capacity)
- Manage staff members and assignments
- Create and manage bookings with availability checks
- Simple admin UI using server-side rendered templates (Jinja2)
- Data persisted in SQLite for simple local/demo deployments

## Stack
- Language: Python 3.8+
- Framework: Flask
- Database: SQLite (via SQLAlchemy or direct SQLite — replace if different)
- Notable libraries (examples; replace as needed): Flask, SQLAlchemy (or Flask-SQLAlchemy), Flask-Migrate, WTForms (or Flask-WTF), Jinja2

## Quickstart

Clone the repo and run locally:

```bash
git clone https://github.com/25f3000628/trekking-management-app.git
cd trekking-management-app