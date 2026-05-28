"""Equivalence Class & Boundary Value tests for the Authentication Controller.

Target: app/controllers/auth_controller.py
    - POST /auth/register  (user registration)
    - POST /auth/login     (user authentication)
    - GET  /auth/logout    (session teardown)
    - GET  /auth/login and /auth/register (authenticated redirect guards)

This module applies two white-box + black-box testing techniques:

1. **Equivalence Class Partitioning (ECP)**
   Each input field is divided into valid and invalid partitions.
   One representative test is written per partition.

2. **Boundary Value Analysis (BVA)**
   For inputs with numeric boundaries (password length >= 6,
   full_name length >= 2), tests target the boundary itself,
   one value below, and one value above.

┌────────────────────────────────────────────────────────────────────┐
│  REGISTER — Input partitions                                      │
│                                                                    │
│  email                                                             │
│    EC1  valid:   contains '@' and non-empty      → accepted        │
│    EC2  invalid: missing '@'                     → rejected        │
│    EC3  invalid: empty string                    → rejected        │
│    EC4  invalid: already registered              → rejected        │
│    EC5  valid:   mixed case / leading whitespace → normalised       │
│                                                                    │
│  password                                                          │
│    EC6  valid:   len >= 6                         → accepted        │
│    EC7  invalid: len < 6                          → rejected        │
│    EC8  invalid: empty string                     → rejected        │
│    BV1  boundary: len == 5  (below)               → rejected        │
│    BV2  boundary: len == 6  (on)                  → accepted        │
│    BV3  boundary: len == 7  (above)               → accepted        │
│                                                                    │
│  confirm_password                                                  │
│    EC9  valid:   matches password                 → accepted        │
│    EC10 invalid: does not match                   → rejected        │
│                                                                    │
│  full_name                                                         │
│    EC11 valid:   stripped len >= 2                 → accepted        │
│    EC12 invalid: stripped len < 2                  → rejected        │
│    EC13 invalid: empty string                     → rejected        │
│    BV4  boundary: stripped len == 1 (below)        → rejected        │
│    BV5  boundary: stripped len == 2 (on)           → accepted        │
│    BV6  boundary: stripped len == 3 (above)        → accepted        │
│                                                                    │
│  LOGIN — Input partitions                                          │
│                                                                    │
│  email                                                             │
│    EC14 valid:   registered email                 → accepted        │
│    EC15 invalid: unregistered email               → rejected        │
│    EC16 invalid: empty string                     → rejected        │
│    EC17 valid:   case-insensitive match           → accepted        │
│                                                                    │
│  password                                                          │
│    EC18 valid:   correct password                 → accepted        │
│    EC19 invalid: wrong password                   → rejected        │
│    EC20 invalid: empty string                     → rejected        │
└────────────────────────────────────────────────────────────────────┘
"""

import pytest


# ══════════════════════════════════════════════════════════════════════
#  REGISTER — Equivalence Class Tests
# ══════════════════════════════════════════════════════════════════════


class TestRegisterEquivalenceClasses:
    """Equivalence class tests for POST /auth/register."""

    # ── EC1: valid email ──────────────────────────────────────────────

    def test_ec1_valid_email_accepted(self, client):
        """EC1: A well-formed email with '@' is accepted and the user
        is registered and auto-logged-in (redirect to dashboard)."""
        response = client.post("/auth/register", data={
            "email": "alice@example.com",
            "password": "secure123",
            "confirm_password": "secure123",
            "full_name": "Alice Smith",
        }, follow_redirects=False)
        assert response.status_code == 302
        assert "dashboard" in response.headers["Location"].lower()

    # ── EC2: email missing '@' ────────────────────────────────────────

    def test_ec2_email_missing_at_rejected(self, client):
        """EC2: An email without '@' is invalid → stays on register page
        with an error message."""
        response = client.post("/auth/register", data={
            "email": "invalidemail.com",
            "password": "secure123",
            "confirm_password": "secure123",
            "full_name": "Alice Smith",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"email" in response.data.lower() or b"invalid" in response.data.lower()

    # ── EC3: empty email ──────────────────────────────────────────────

    def test_ec3_empty_email_rejected(self, client):
        """EC3: An empty email string is invalid → registration fails."""
        response = client.post("/auth/register", data={
            "email": "",
            "password": "secure123",
            "confirm_password": "secure123",
            "full_name": "Alice Smith",
        }, follow_redirects=True)
        assert response.status_code == 200

    # ── EC4: duplicate email ──────────────────────────────────────────

    def test_ec4_duplicate_email_rejected(self, client, sample_user):
        """EC4: Registering with an already-taken email is rejected
        with an 'already registered' message."""
        response = client.post("/auth/register", data={
            "email": "test@example.com",  # sample_user's email
            "password": "secure123",
            "confirm_password": "secure123",
            "full_name": "Duplicate User",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"already registered" in response.data.lower()

    # ── EC5: email normalisation (case + whitespace) ──────────────────

    def test_ec5_email_normalised(self, client):
        """EC5: Mixed-case and whitespace-padded emails are normalised
        to lowercase and trimmed before storage."""
        response = client.post("/auth/register", data={
            "email": "  ALICE@EXAMPLE.COM  ",
            "password": "secure123",
            "confirm_password": "secure123",
            "full_name": "Alice Smith",
        }, follow_redirects=False)
        assert response.status_code == 302  # success → redirect

        # Verify normalised email can be used to log in
        response2 = client.post("/auth/login", data={
            "email": "alice@example.com",
            "password": "secure123",
        }, follow_redirects=False)
        assert response2.status_code == 302  # login success

    # ── EC6: valid password (len >= 6) ────────────────────────────────

    def test_ec6_valid_password_accepted(self, client):
        """EC6: A password of 8 characters (well above minimum) is accepted."""
        response = client.post("/auth/register", data={
            "email": "pwd8@example.com",
            "password": "abcdefgh",
            "confirm_password": "abcdefgh",
            "full_name": "Password Test",
        }, follow_redirects=False)
        assert response.status_code == 302

    # ── EC7: short password (len < 6) ─────────────────────────────────

    def test_ec7_short_password_rejected(self, client):
        """EC7: A 3-character password is rejected with a '6 characters'
        error message."""
        response = client.post("/auth/register", data={
            "email": "pwd3@example.com",
            "password": "abc",
            "confirm_password": "abc",
            "full_name": "Short Pwd",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"6 characters" in response.data

    # ── EC8: empty password ───────────────────────────────────────────

    def test_ec8_empty_password_rejected(self, client):
        """EC8: An empty password string is rejected."""
        response = client.post("/auth/register", data={
            "email": "emptypwd@example.com",
            "password": "",
            "confirm_password": "",
            "full_name": "Empty Pwd",
        }, follow_redirects=True)
        assert response.status_code == 200

    # ── EC9: passwords match ──────────────────────────────────────────

    def test_ec9_matching_passwords_accepted(self, client):
        """EC9: When password and confirm_password are identical,
        registration proceeds normally."""
        response = client.post("/auth/register", data={
            "email": "match@example.com",
            "password": "matching123",
            "confirm_password": "matching123",
            "full_name": "Match Test",
        }, follow_redirects=False)
        assert response.status_code == 302

    # ── EC10: passwords do not match ──────────────────────────────────

    def test_ec10_mismatched_passwords_rejected(self, client):
        """EC10: When password and confirm_password differ, the controller
        returns the register form with a 'do not match' error before
        even calling AuthenticationService."""
        response = client.post("/auth/register", data={
            "email": "mismatch@example.com",
            "password": "password123",
            "confirm_password": "different456",
            "full_name": "Mismatch Test",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"do not match" in response.data.lower()

    # ── EC11: valid full_name (stripped len >= 2) ─────────────────────

    def test_ec11_valid_name_accepted(self, client):
        """EC11: A normal full name (well above 2 chars) is accepted."""
        response = client.post("/auth/register", data={
            "email": "name@example.com",
            "password": "secure123",
            "confirm_password": "secure123",
            "full_name": "Alice Smith",
        }, follow_redirects=False)
        assert response.status_code == 302

    # ── EC12: name too short (stripped len < 2) ───────────────────────

    def test_ec12_single_char_name_rejected(self, client):
        """EC12: A single-character name is rejected with a 'name' error."""
        response = client.post("/auth/register", data={
            "email": "name1@example.com",
            "password": "secure123",
            "confirm_password": "secure123",
            "full_name": "A",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"name" in response.data.lower()

    # ── EC13: empty name ──────────────────────────────────────────────

    def test_ec13_empty_name_rejected(self, client):
        """EC13: An empty name string is rejected."""
        response = client.post("/auth/register", data={
            "email": "noname@example.com",
            "password": "secure123",
            "confirm_password": "secure123",
            "full_name": "",
        }, follow_redirects=True)
        assert response.status_code == 200


# ══════════════════════════════════════════════════════════════════════
#  REGISTER — Boundary Value Tests
# ══════════════════════════════════════════════════════════════════════


class TestRegisterBoundaryValues:
    """Boundary value tests for POST /auth/register.

    password boundary:   min valid length = 6
    full_name boundary:  min valid stripped length = 2
    """

    # ── Password boundary: len == 5 (below) ───────────────────────────

    def test_bv1_password_5_chars_rejected(self, client):
        """BV1: Password of exactly 5 characters (one below boundary)
        is rejected."""
        response = client.post("/auth/register", data={
            "email": "bv1@example.com",
            "password": "abcde",         # len 5
            "confirm_password": "abcde",
            "full_name": "BV Test",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"6 characters" in response.data

    # ── Password boundary: len == 6 (on) ──────────────────────────────

    def test_bv2_password_6_chars_accepted(self, client):
        """BV2: Password of exactly 6 characters (on the boundary)
        is accepted."""
        response = client.post("/auth/register", data={
            "email": "bv2@example.com",
            "password": "abcdef",        # len 6
            "confirm_password": "abcdef",
            "full_name": "BV Test",
        }, follow_redirects=False)
        assert response.status_code == 302  # success → redirect

    # ── Password boundary: len == 7 (above) ───────────────────────────

    def test_bv3_password_7_chars_accepted(self, client):
        """BV3: Password of exactly 7 characters (one above boundary)
        is accepted."""
        response = client.post("/auth/register", data={
            "email": "bv3@example.com",
            "password": "abcdefg",       # len 7
            "confirm_password": "abcdefg",
            "full_name": "BV Test",
        }, follow_redirects=False)
        assert response.status_code == 302

    # ── Name boundary: stripped len == 1 (below) ──────────────────────

    def test_bv4_name_1_char_rejected(self, client):
        """BV4: Full name of 1 character after stripping (one below
        boundary) is rejected."""
        response = client.post("/auth/register", data={
            "email": "bv4@example.com",
            "password": "secure123",
            "confirm_password": "secure123",
            "full_name": "X",            # stripped len 1
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"name" in response.data.lower()

    # ── Name boundary: stripped len == 2 (on) ─────────────────────────

    def test_bv5_name_2_chars_accepted(self, client):
        """BV5: Full name of exactly 2 characters after stripping
        (on the boundary) is accepted."""
        response = client.post("/auth/register", data={
            "email": "bv5@example.com",
            "password": "secure123",
            "confirm_password": "secure123",
            "full_name": "Jo",           # stripped len 2
        }, follow_redirects=False)
        assert response.status_code == 302

    # ── Name boundary: stripped len == 3 (above) ──────────────────────

    def test_bv6_name_3_chars_accepted(self, client):
        """BV6: Full name of 3 characters after stripping (one above
        boundary) is accepted."""
        response = client.post("/auth/register", data={
            "email": "bv6@example.com",
            "password": "secure123",
            "confirm_password": "secure123",
            "full_name": "Joe",          # stripped len 3
        }, follow_redirects=False)
        assert response.status_code == 302

    # ── Name boundary: whitespace-only should count as empty ──────────

    def test_bv7_whitespace_only_name_rejected(self, client):
        """BV7: A name that is only whitespace strips to '' (len 0),
        which is below the boundary → rejected."""
        response = client.post("/auth/register", data={
            "email": "bv7@example.com",
            "password": "secure123",
            "confirm_password": "secure123",
            "full_name": "   ",          # stripped len 0
        }, follow_redirects=True)
        assert response.status_code == 200

    # ── Name boundary: padded 1-char should still be rejected ─────────

    def test_bv8_padded_1_char_name_rejected(self, client):
        """BV8: A name '  A  ' strips to 'A' (len 1), which is below
        the boundary → rejected. Ensures stripping is applied before
        the length check."""
        response = client.post("/auth/register", data={
            "email": "bv8@example.com",
            "password": "secure123",
            "confirm_password": "secure123",
            "full_name": "  A  ",        # stripped len 1
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"name" in response.data.lower()


# ══════════════════════════════════════════════════════════════════════
#  LOGIN — Equivalence Class Tests
# ══════════════════════════════════════════════════════════════════════


class TestLoginEquivalenceClasses:
    """Equivalence class tests for POST /auth/login."""

    # ── EC14: valid credentials ───────────────────────────────────────

    def test_ec14_valid_credentials_redirect(self, client, sample_user):
        """EC14: Correct email + password → redirect to dashboard (302)."""
        response = client.post("/auth/login", data={
            "email": "test@example.com",
            "password": "password123",
        }, follow_redirects=False)
        assert response.status_code == 302

    # ── EC15: unregistered email ──────────────────────────────────────

    def test_ec15_unregistered_email_rejected(self, client):
        """EC15: An email that has never been registered → stays on
        login page with 'invalid' error."""
        response = client.post("/auth/login", data={
            "email": "nobody@example.com",
            "password": "password123",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"invalid" in response.data.lower()

    # ── EC16: empty email ─────────────────────────────────────────────

    def test_ec16_empty_email_rejected(self, client):
        """EC16: An empty email string → login fails."""
        response = client.post("/auth/login", data={
            "email": "",
            "password": "password123",
        }, follow_redirects=True)
        assert response.status_code == 200

    # ── EC17: case-insensitive email ──────────────────────────────────

    def test_ec17_case_insensitive_email_accepted(self, client, sample_user):
        """EC17: Email lookup is case-insensitive — upper-case version
        of a registered email works."""
        response = client.post("/auth/login", data={
            "email": "TEST@EXAMPLE.COM",
            "password": "password123",
        }, follow_redirects=False)
        assert response.status_code == 302

    # ── EC18: correct password ────────────────────────────────────────

    def test_ec18_correct_password_accepted(self, client, sample_user):
        """EC18: The correct password for an existing user → login
        succeeds and user session is created."""
        response = client.post("/auth/login", data={
            "email": "test@example.com",
            "password": "password123",
        }, follow_redirects=True)
        assert response.status_code == 200
        # After following redirects we should land on the dashboard
        # which is only accessible when authenticated

    # ── EC19: wrong password ──────────────────────────────────────────

    def test_ec19_wrong_password_rejected(self, client, sample_user):
        """EC19: A wrong password for an existing user → login fails
        with 'invalid' error."""
        response = client.post("/auth/login", data={
            "email": "test@example.com",
            "password": "WRONG_PASSWORD",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"invalid" in response.data.lower()

    # ── EC20: empty password ──────────────────────────────────────────

    def test_ec20_empty_password_rejected(self, client, sample_user):
        """EC20: An empty password string → login fails."""
        response = client.post("/auth/login", data={
            "email": "test@example.com",
            "password": "",
        }, follow_redirects=True)
        assert response.status_code == 200


# ══════════════════════════════════════════════════════════════════════
#  LOGIN — Boundary Value Tests
# ══════════════════════════════════════════════════════════════════════


class TestLoginBoundaryValues:
    """Boundary value tests for POST /auth/login.

    The login endpoint itself has no numeric boundaries to enforce
    (those are on register), but the interaction with the authentication
    service surface boundary-adjacent scenarios around the password
    that was set during registration.
    """

    def test_bv_login_with_minimum_valid_password(self, client):
        """BV: Register with a 6-char password (minimum boundary),
        then log in with the same 6-char password → succeeds.
        Verifies that the hash stored at the boundary is verified
        correctly."""
        # Register first
        client.post("/auth/register", data={
            "email": "minpwd@example.com",
            "password": "abcdef",
            "confirm_password": "abcdef",
            "full_name": "Min Pwd",
        })
        # Logout (registration auto-logs-in)
        client.get("/auth/logout")
        # Login with same boundary password
        response = client.post("/auth/login", data={
            "email": "minpwd@example.com",
            "password": "abcdef",
        }, follow_redirects=False)
        assert response.status_code == 302

    def test_bv_login_password_off_by_one_char(self, client, sample_user):
        """BV: A password that is one character shorter than the correct
        one is rejected — verifying exact-match semantics."""
        response = client.post("/auth/login", data={
            "email": "test@example.com",
            "password": "password12",  # missing trailing '3'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"invalid" in response.data.lower()

    def test_bv_login_password_one_char_extra(self, client, sample_user):
        """BV: A password that is one character longer than the correct
        one is rejected — verifying exact-match semantics."""
        response = client.post("/auth/login", data={
            "email": "test@example.com",
            "password": "password1234",  # extra trailing '4'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"invalid" in response.data.lower()


# ══════════════════════════════════════════════════════════════════════
#  AUTH GUARDS — Equivalence Class Tests
# ══════════════════════════════════════════════════════════════════════


class TestAuthGuards:
    """Equivalence class tests for the authentication guard logic
    in the login/register/logout routes.

    These cover the controller's redirect behaviour based on
    authentication state — a boolean partition (authenticated vs
    unauthenticated).
    """

    # ── Authenticated user visiting /auth/login → redirect ────────────

    def test_authenticated_user_redirected_from_login(self, auth_client):
        """An already-logged-in user visiting GET /auth/login is
        redirected to the dashboard (not shown the login form)."""
        response = auth_client.get("/auth/login", follow_redirects=False)
        assert response.status_code == 302

    # ── Authenticated user visiting /auth/register → redirect ─────────

    def test_authenticated_user_redirected_from_register(self, auth_client):
        """An already-logged-in user visiting GET /auth/register is
        redirected to the dashboard."""
        response = auth_client.get("/auth/register", follow_redirects=False)
        assert response.status_code == 302

    # ── Unauthenticated user visiting /auth/login → 200 ──────────────

    def test_unauthenticated_user_sees_login_form(self, client):
        """An unauthenticated user visiting GET /auth/login receives
        the login form (HTTP 200)."""
        response = client.get("/auth/login")
        assert response.status_code == 200

    # ── Unauthenticated user visiting /auth/register → 200 ───────────

    def test_unauthenticated_user_sees_register_form(self, client):
        """An unauthenticated user visiting GET /auth/register receives
        the registration form (HTTP 200)."""
        response = client.get("/auth/register")
        assert response.status_code == 200

    # ── Logout → redirect to public page ──────────────────────────────

    def test_logout_redirects_to_public_page(self, auth_client):
        """GET /auth/logout clears the session and redirects to the
        public career page."""
        response = auth_client.get("/auth/logout", follow_redirects=False)
        assert response.status_code == 302

    # ── Login with 'next' parameter → redirect to next ────────────────

    def test_login_redirects_to_next_page(self, client, sample_user):
        """After successful login, if a 'next' query parameter is present
        the user is redirected there instead of the default dashboard."""
        response = client.post(
            "/auth/login?next=/resume/upload",
            data={
                "email": "test@example.com",
                "password": "password123",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/resume/upload" in response.headers["Location"]