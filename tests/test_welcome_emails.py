from unittest.mock import patch

from api.utils.email import send_couple_connected_email, send_welcome_account_email


def test_send_welcome_account_email():
    with patch("api.utils.email.send_brevo_email", return_value=True) as mock_send:
        success = send_welcome_account_email("alice@example.com", "Alice", "JOIN1234")
        assert success is True
        assert mock_send.call_count == 1
        to_email, to_name, subject, html = mock_send.call_args[0]
        assert to_email == "alice@example.com"
        assert to_name == "Alice"
        assert "Welcome to us, Alice" in subject
        assert "JOIN1234" in html
        assert "us<span style=\"color: #ff007f;\">.</span>" in html


def test_send_couple_connected_email():
    with patch("api.utils.email.send_brevo_email", return_value=True) as mock_send:
        success = send_couple_connected_email("bob@example.com", "Bob", "Alice")
        assert success is True
        assert mock_send.call_count == 1
        to_email, to_name, subject, html = mock_send.call_args[0]
        assert to_email == "bob@example.com"
        assert to_name == "Bob"
        assert "Alice" in subject
        assert "Bob" in html
        assert "Alice" in html
        assert "connected" in html.lower()
