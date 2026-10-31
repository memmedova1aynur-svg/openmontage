"""İstifadəçiyə göstərilən xətalar: səbəb + istifadəçinin edə biləcəyi addım."""

from __future__ import annotations


class UserError(Exception):
    def __init__(self, message: str, hint: str = "", detail: str = ""):
        super().__init__(message)
        self.message = message
        self.hint = hint
        self.detail = detail

    def to_dict(self) -> dict:
        return {"error": self.message, "hint": self.hint}
