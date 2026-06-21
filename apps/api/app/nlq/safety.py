"""Safety utilities for escaping untrusted dataset content in LLM prompts."""

from __future__ import annotations


def escape_untrusted_data(value: str | None) -> str:
    """Wrap untrusted data (like raw CSV headers or sample values) in clear delimiters.

    This is a defense-in-depth measure against prompt injection. Even if a malicious
    actor crafted a CSV with a column named "ignore previous instructions and...",
    the prompt structure makes clear to the model that this string is data, not a directive.

    The real safety boundary is that the model's output is JSON validated against
    an allow-list, not the prompt wording itself.
    """
    if value is None:
        return "null"

    # Convert to string and neutralise any literal occurrences of the closing tag
    # to prevent a payload from prematurely breaking out of the block.
    safe_value = str(value).replace("</untrusted_dataset_content>", "")

    return f"<untrusted_dataset_content>{safe_value}</untrusted_dataset_content>"
