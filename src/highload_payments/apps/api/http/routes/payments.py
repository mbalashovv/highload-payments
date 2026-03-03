from fastapi import APIRouter, Depends, Request, Response, status

from highload_payments.application.dto.commands import CreatePaymentCommand
from highload_payments.application.use_cases.create_payment import CreatePaymentUseCase
from highload_payments.apps.api.http.schemas import (
    CreatePaymentRequest,
    CreatePaymentResponse,
)


payments_router = APIRouter()


def get_create_payment_use_case(request: Request) -> CreatePaymentUseCase:
    return request.app.state.create_payment_use_case


@payments_router.post(
    "/payments",
    response_model=CreatePaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    payload: CreatePaymentRequest,
    response: Response,
    use_case: CreatePaymentUseCase = Depends(get_create_payment_use_case),
) -> CreatePaymentResponse:
    result = await use_case.execute(
        CreatePaymentCommand(
            account_id=payload.account_id,
            amount_minor=payload.amount_minor,
            currency=payload.currency,
            idempotency_key=payload.idempotency_key,
        )
    )
    if result.duplicated:
        response.status_code = status.HTTP_200_OK

    return CreatePaymentResponse(
        payment_id=result.payment_id,
        status=result.status.value,
        duplicated=result.duplicated,
    )
