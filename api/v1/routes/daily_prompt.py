from fastapi import APIRouter, HTTPException, status

from api.core.dependencies import CurrentUser, DatabaseSession
from api.v1.schema.daily_prompt import AnswerPromptRequest, DailyPromptResponse
from api.v1.services.daily_prompt import (
    answer_daily_prompt,
    get_or_create_daily_prompt,
    serialize_daily_prompt,
)

router = APIRouter(prefix="/daily-prompt", tags=["daily-prompt"])


@router.get("", response_model=DailyPromptResponse)
def get_daily_prompt(db: DatabaseSession, user: CurrentUser) -> DailyPromptResponse:
    try:
        prompt = get_or_create_daily_prompt(db, user)
        return serialize_daily_prompt(prompt, user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/answer", response_model=DailyPromptResponse)
async def post_answer(
    payload: AnswerPromptRequest, db: DatabaseSession, user: CurrentUser
) -> DailyPromptResponse:
    try:
        from api.core.realtime import hub
        from api.v1.services.engagement import partner_id_for

        prompt = answer_daily_prompt(db, user, payload.answer)
        pid = partner_id_for(db, user.id)
        await hub.publish(pid, {"type": "today_updated", "prompt_id": str(prompt.id)})
        if pid and not hub.is_online(pid):
            from api.v1.services.push import send_push
            send_push(
                db=db,
                user_id=pid,
                title="us.",
                body=f"{user.name} answered today's question",
                url="/",
                urgency="normal",
                tag="answer",
            )
        return serialize_daily_prompt(prompt, user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

