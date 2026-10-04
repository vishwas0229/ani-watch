from ani_watch.providers.telegram_gateway import TelegramStreamingGateway


def test_range_parser_supports_full_and_open_ranges() -> None:
    assert TelegramStreamingGateway._parse_range(None, 100) is None
    assert TelegramStreamingGateway._parse_range("bytes=10-19", 100) == (10, 19)
    assert TelegramStreamingGateway._parse_range("bytes=10-", 100) == (10, 99)


def test_range_parser_supports_suffix_ranges() -> None:
    assert TelegramStreamingGateway._parse_range("bytes=-10", 100) == (90, 99)


def test_range_parser_rejects_multiple_or_invalid_ranges() -> None:
    import pytest

    with pytest.raises(ValueError):
        TelegramStreamingGateway._parse_range("bytes=0-1,2-3", 100)

    with pytest.raises(ValueError):
        TelegramStreamingGateway._parse_range("bytes=100-120", 100)
