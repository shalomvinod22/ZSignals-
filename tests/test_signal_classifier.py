"""Tests for signal classifier."""

from src.signal_classifier import SignalClassifier


def test_complaint_detection() -> None:
    """Test detection of complaint signal."""
    content = "42% bounce rate with Apollo. Wasted money. Frustrated."
    signals = SignalClassifier.classify(content)
    assert "complaint" in signals


def test_hiring_signal() -> None:
    """Test detection of hiring signal."""
    content = "We're hiring our first SDR for the team."
    signals = SignalClassifier.classify(content)
    assert "hiring" in signals


def test_comparison_shopping() -> None:
    """Test detection of comparison shopping signal."""
    content = "Evaluating alternatives to Apollo. Looking for better data."
    signals = SignalClassifier.classify(content)
    assert "comparison_shopping" in signals


def test_stack_describing() -> None:
    """Test detection of stack describing signal."""
    content = "Our outbound stack: Apollo, Instantly, Clay."
    signals = SignalClassifier.classify(content)
    assert "stack_describing" in signals


def test_vp_hire_signal() -> None:
    """Test detection of VP hire signal."""
    content = "New VP Sales started yesterday at our Series B company."
    signals = SignalClassifier.classify(content)
    assert "vp_hire" in signals


def test_funding_signal() -> None:
    """Test detection of funding signal."""
    content = "Just closed our Series A round."
    signals = SignalClassifier.classify(content)
    assert "funding" in signals


def test_multiple_signals_one_post() -> None:
    """Test detecting multiple signals in one post."""
    content = "We just raised Series A, hired our first SDR, and we're shopping for alternatives to Apollo."
    signals = SignalClassifier.classify(content)
    
    assert "funding" in signals
    assert "hiring" in signals
    assert "comparison_shopping" in signals


def test_no_signals_returns_empty_list() -> None:
    """Test that posts with no signals return empty list."""
    content = "Just a random comment about sales."
    signals = SignalClassifier.classify(content)
    assert signals == []


def test_case_insensitive() -> None:
    """Test that detection is case-insensitive."""
    content = "HIRING SDR for the team!"
    signals = SignalClassifier.classify(content)
    assert "hiring" in signals


def test_empty_content() -> None:
    """Test handling of empty content."""
    signals = SignalClassifier.classify("")
    assert signals == []


def test_none_content() -> None:
    """Test handling of None content."""
    signals = SignalClassifier.classify(None)  # type: ignore
    assert signals == []
