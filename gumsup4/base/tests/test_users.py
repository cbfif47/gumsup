"""Tests for users model."""


from gumsup4.base.models import User


def test_user_tablename():
    """Tablename test && Example pytest test."""

    assert User._meta.db_table == "users"
