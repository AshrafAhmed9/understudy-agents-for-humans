"""A do-nothing Model, purely so Agent() can be constructed in tests without
strands-agents defaulting to BedrockModel and reaching for AWS credentials
this machine doesn't have configured. None of these tests invoke the model —
stream() is never actually called; the methods exist only to satisfy the
Model base class.
"""

from __future__ import annotations

from typing import Any

from strands.models.model import Model


class NullModel(Model):
    stateful = False

    def get_config(self) -> Any:
        return {}

    def update_config(self, **model_config: Any) -> None:
        pass

    async def stream(self, *args, **kwargs):
        if False:  # pragma: no cover - never actually invoked in these tests
            yield {}

    async def structured_output(self, *args, **kwargs):
        if False:  # pragma: no cover
            yield {}
