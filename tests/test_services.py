"""Tests for service layer business logic."""
from app.services.event_service import compute_idempotency_key
from app.services.subscription_service import (
    create_subscription,
    list_subscriptions,
    get_matching_subscriptions,
)


def test_idempotency_key_deterministic():
    """Same inputs should produce the same idempotency key."""
    key1 = compute_idempotency_key("src", "type", {"a": 1})
    key2 = compute_idempotency_key("src", "type", {"a": 1})
    assert key1 == key2


def test_idempotency_key_different_inputs():
    """Different inputs should produce different keys."""
    key1 = compute_idempotency_key("src", "type", {"a": 1})
    key2 = compute_idempotency_key("src", "type", {"a": 2})
    assert key1 != key2


def test_idempotency_key_order_independent():
    """JSON key order should not affect the idempotency key."""
    key1 = compute_idempotency_key("src", "type", {"a": 1, "b": 2})
    key2 = compute_idempotency_key("src", "type", {"b": 2, "a": 1})
    assert key1 == key2


def test_matching_subscriptions_exact_match(db_session):
    """get_matching_subscriptions should find exact matches."""
    create_subscription(db_session, "svc", "push", "github.com", "https://hook.com/a")
    matches = get_matching_subscriptions(db_session, "push", "github.com")
    assert len(matches) == 1
    assert matches[0].consumer_id == "svc"


def test_matching_subscriptions_wildcard_type(db_session):
    """Subscription with event_type=None should match all types."""
    create_subscription(db_session, "svc", None, "github.com", "https://hook.com/a")
    matches = get_matching_subscriptions(db_session, "push", "github.com")
    assert len(matches) == 1


def test_matching_subscriptions_wildcard_source(db_session):
    """Subscription with source=None should match all sources."""
    create_subscription(db_session, "svc", "push", None, "https://hook.com/a")
    matches = get_matching_subscriptions(db_session, "push", "github.com")
    assert len(matches) == 1


def test_matching_subscriptions_no_webhook(db_session):
    """Subscriptions without webhook_url should not be returned."""
    create_subscription(db_session, "svc", "push", "github.com", None)
    matches = get_matching_subscriptions(db_session, "push", "github.com")
    assert len(matches) == 0


def test_matching_subscriptions_no_match(db_session):
    """Non-matching subscriptions should not be returned."""
    create_subscription(db_session, "svc", "push", "github.com", "https://hook.com/a")
    matches = get_matching_subscriptions(db_session, "pull_request", "gitlab.com")
    assert len(matches) == 0


def test_list_subscriptions_all(db_session):
    """list_subscriptions without filter returns all."""
    create_subscription(db_session, "a", None, None, None)
    create_subscription(db_session, "b", None, None, None)
    subs = list_subscriptions(db_session)
    assert len(subs) == 2


def test_list_subscriptions_filtered(db_session):
    """list_subscriptions with consumer_id filter returns only matching."""
    create_subscription(db_session, "a", None, None, None)
    create_subscription(db_session, "b", None, None, None)
    subs = list_subscriptions(db_session, "a")
    assert len(subs) == 1
    assert subs[0].consumer_id == "a"
