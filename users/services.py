from decimal import Decimal

import stripe
from django.conf import settings


class StripeServiceError(Exception):
    """Ошибка взаимодействия со Stripe."""


def configure_stripe() -> None:
    """Устанавливает секретный ключ Stripe."""

    if not settings.STRIPE_SECRET_KEY:
        raise StripeServiceError(
            "Секретный ключ Stripe не настроен."
        )

    stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_product(course):
    """Создаёт продукт Stripe для курса."""

    configure_stripe()

    try:
        return stripe.Product.create(
            name=course.title,
            description=course.description or "",
            metadata={
                "course_id": str(course.pk),
            },
        )
    except stripe.StripeError as error:
        raise StripeServiceError(
            f"Не удалось создать продукт Stripe: {error}"
        ) from error


def create_stripe_price(
    product_id: str,
    amount: Decimal,
):
    """Создаёт цену Stripe в копейках."""

    configure_stripe()

    amount_in_kopecks = int(
        amount * Decimal("100")
    )

    if amount_in_kopecks <= 0:
        raise StripeServiceError(
            "Сумма платежа должна быть больше нуля."
        )

    try:
        return stripe.Price.create(
            product=product_id,
            unit_amount=amount_in_kopecks,
            currency="rub",
        )
    except stripe.StripeError as error:
        raise StripeServiceError(
            f"Не удалось создать цену Stripe: {error}"
        ) from error


def create_checkout_session(
    price_id: str,
    payment_id: int,
):
    """Создаёт Stripe Checkout Session."""

    configure_stripe()

    try:
        return stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                },
            ],
            success_url=(
                settings.STRIPE_SUCCESS_URL
                + "?session_id={CHECKOUT_SESSION_ID}"
            ),
            cancel_url=settings.STRIPE_CANCEL_URL,
            client_reference_id=str(payment_id),
            metadata={
                "payment_id": str(payment_id),
            },
        )
    except stripe.StripeError as error:
        raise StripeServiceError(
            f"Не удалось создать сессию Stripe: {error}"
        ) from error


def retrieve_checkout_session(
    session_id: str,
):
    """Получает актуальное состояние сессии."""

    configure_stripe()

    try:
        return stripe.checkout.Session.retrieve(
            session_id,
        )
    except stripe.StripeError as error:
        raise StripeServiceError(
            f"Не удалось проверить платёж Stripe: {error}"
        ) from error

def retrieve_checkout_session(
    session_id: str,
):
    """Получает акту текущий статус сессии Stripe."""

    configure_stripe()

    try:
        return stripe.checkout.Session.retrieve(
            session_id,
        )
    except stripe.StripeError as error:
        raise StripeServiceError(
            "Не удалось получить статус платежа "
            f"Stripe: {error}"
        ) from error