from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.routers.v1.planning_router import check_rate_limit


def test_rate_limit_allows_under_limit():
    mock_redis = MagicMock()
    mock_redis.pipeline.return_value.execute.return_value = [5, True]

    with patch("app.routers.v1.planning_router.get_redis", return_value=mock_redis):
        check_rate_limit(customer_id=1)


def test_rate_limit_blocks_over_limit():
    mock_redis = MagicMock()
    mock_redis.pipeline.return_value.execute.return_value = [11, True]

    with patch("app.routers.v1.planning_router.get_redis", return_value=mock_redis):
        with pytest.raises(HTTPException) as exc:
            check_rate_limit(customer_id=1)

    assert exc.value.status_code == 429


def test_rate_limit_fails_open_when_redis_unavailable():
    with patch("app.routers.v1.planning_router.get_redis", return_value=None):
        check_rate_limit(customer_id=1)


def test_different_customers_have_separate_rate_limits():
    captured_keys = []

    def fake_pipeline():
        mock_pipe = MagicMock()

        def execute():
            return [1, True]

        mock_pipe.execute = execute
        mock_pipe.incr = lambda key: captured_keys.append(key)
        mock_pipe.expire = MagicMock()
        return mock_pipe

    mock_redis = MagicMock()
    mock_redis.pipeline = fake_pipeline

    with patch("app.routers.v1.planning_router.get_redis", return_value=mock_redis):
        check_rate_limit(customer_id=1)
        check_rate_limit(customer_id=2)

    assert len(set(captured_keys)) == 2
