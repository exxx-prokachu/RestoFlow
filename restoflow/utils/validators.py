import re
from datetime import datetime


class ValidationError(ValueError):
    pass


USERNAME_RE = re.compile(r"^[a-zA-Z0-9._-]{3,30}$")
EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
NAME_RE = re.compile(r"^[a-zA-Zа-яА-ЯёЁ\- ]{2,60}$")


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    if len(digits) == 10:
        digits = "7" + digits
    return digits


def format_phone(digits: str) -> str:
    if len(digits) != 11:
        return digits
    return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:]}"


def validate_phone(phone: str) -> str:
    digits = normalize_phone(phone)
    if len(digits) != 11 or not digits.startswith("7"):
        raise ValidationError("Телефон: формат +7 (900) 000-00-00")
    return digits


def password_strength(password: str) -> dict:
    checks = {
        "length": len(password or "") >= 8,
        "lower": bool(re.search(r"[a-zа-яё]", password or "")),
        "upper": bool(re.search(r"[A-ZА-ЯЁ]", password or "")),
        "digit": bool(re.search(r"\d", password or "")),
        "special": bool(re.search(r"[^a-zA-Z0-9а-яА-ЯёЁ]", password or "")),
    }
    score = sum(checks.values())
    labels = {0: "очень слабый", 1: "слабый", 2: "средний",
              3: "хороший", 4: "сильный", 5: "отличный"}
    return {"score": score, "label": labels[score], **checks}


def validate_password(password: str, min_score: int = 2) -> str:
    if not password or len(password) < 6:
        raise ValidationError("Пароль: минимум 6 символов")
    if len(password) > 72:
        raise ValidationError("Пароль: максимум 72 символа")
    if password_strength(password)["score"] < min_score:
        raise ValidationError("Пароль простой: добавьте цифры и разный регистр")
    return password


def validate_username(username: str) -> str:
    value = (username or "").strip()
    if not USERNAME_RE.match(value):
        raise ValidationError("Логин: 3–30 символов, латиница, цифры, . _ -")
    return value


def validate_email(email: str | None) -> str | None:
    if not email or not email.strip():
        return None
    value = email.strip().lower()
    if not EMAIL_RE.match(value):
        raise ValidationError("Email: некорректный формат")
    return value


def validate_full_name(name: str) -> str:
    value = " ".join((name or "").split())
    if not NAME_RE.match(value):
        raise ValidationError("ФИО: буквы, дефис, пробел (2–60 символов)")
    return value


def validate_address(address: str | None) -> str | None:
    if address is None:
        return None
    value = " ".join(address.split())
    if len(value) < 10 or len(value) > 200:
        raise ValidationError("Адрес: от 10 до 200 символов")
    if not re.search(r"\d", value):
        raise ValidationError("Адрес: укажите дом/квартиру (цифры)")
    return value


def validate_text(text: str | None, max_len: int = 1000,
                  field: str = "Текст") -> str | None:
    if text is None:
        return None
    value = text.strip()
    if len(value) > max_len:
        raise ValidationError(f"{field}: не длиннее {max_len} символов")
    return value or None


def validate_rating(rating: int) -> int:
    if not 1 <= rating <= 5:
        raise ValidationError("Оценка: от 1 до 5")
    return rating


def validate_table(number: int | None) -> int | None:
    if number is None:
        return None
    if not 1 <= number <= 200:
        raise ValidationError("Номер стола: от 1 до 200")
    return number

def luhn_check(number: str) -> bool:
    total = 0
    for i, d in enumerate(reversed([int(x) for x in number])):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def validate_card_number(card: str) -> str:
    digits = re.sub(r"\D", "", card or "")
    if len(digits) != 16 or not luhn_check(digits):
        raise ValidationError("Карта: 16 цифр, контрольная сумма не сходится")
    return digits


def validate_card_exp(exp: str) -> str:
    m = re.fullmatch(r"(0[1-9]|1[0-2])\s*/\s*(\d{2})", exp or "")
    if not m:
        raise ValidationError("Срок карты: формат MM/YY")
    month, year = int(m.group(1)), 2000 + int(m.group(2))
    now = datetime.now()
    if year < now.year or (year == now.year and month < now.month):
        raise ValidationError("Срок действия карты истёк")
    return f"{month % 100:02d}/{year % 100:02d}"


def validate_cvc(cvc: str) -> str:
    if not re.fullmatch(r"\d{3}", cvc or ""):
        raise ValidationError("CVC: ровно 3 цифры")
    return cvc