from perplexity_polza_mcp_server.server import _format_response


def test_format_response_includes_usage() -> None:
    response = {
        "choices": [
            {
                "message": {
                    "content": "Hello",
                }
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
            "cost_rub": 0.15,
        },
    }

    result = _format_response(response)

    assert "Hello" in result
    assert "Usage: prompt_tokens=10, completion_tokens=20, total_tokens=30, cost_rub=0.15" in result
