from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.v1.models import Answer, Couple, DailyPrompt, Question, User
from api.v1.schema.daily_prompt import DailyPromptResponse, QuestionOut
from api.v1.services.engagement import couple_id_for


def get_or_create_daily_prompt(db: Session, user: User) -> DailyPrompt:
    couple_id = couple_id_for(db, user.id)
    today = datetime.now(timezone.utc).date()

    prompt = db.scalar(
        select(DailyPrompt).where(
            DailyPrompt.couple_id == couple_id,
            DailyPrompt.prompt_date == today,
        )
    )
    if prompt is not None:
        return prompt

    # Pick a question not previously used for daily prompts by this couple
    used_subquery = select(DailyPrompt.question_id).where(DailyPrompt.couple_id == couple_id)
    question = db.scalar(
        select(Question)
        .where(
            Question.active.is_(True),
            Question.category != "spicy_18",
            ~Question.id.in_(used_subquery),
        )
        .order_by(func.random())
    )
    if question is None:
        # Fallback to any active non-spicy question if all have been used
        question = db.scalar(
            select(Question)
            .where(Question.active.is_(True), Question.category != "spicy_18")
            .order_by(func.random())
        )

    if question is None:
        raise LookupError("No questions found in database")

    prompt = DailyPrompt(couple_id=couple_id, question_id=question.id, prompt_date=today)
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


def serialize_daily_prompt(prompt: DailyPrompt, user: User) -> DailyPromptResponse:
    my_answer_row = next((a for a in prompt.answers if a.user_id == user.id), None)
    partner_answer_row = next((a for a in prompt.answers if a.user_id != user.id), None)

    my_answer = my_answer_row.body if my_answer_row else None
    partner_answered = partner_answer_row is not None
    both_answered = (my_answer is not None) and partner_answered
    partner_answer = partner_answer_row.body if both_answered else None

    return DailyPromptResponse(
        prompt_id=prompt.id,
        date=prompt.prompt_date,
        question=QuestionOut(
            id=prompt.question.id,
            category=prompt.question.category,
            text=prompt.question.text,
        ),
        my_answer=my_answer,
        partner_answered=partner_answered,
        both_answered=both_answered,
        partner_answer=partner_answer,
    )


def answer_daily_prompt(db: Session, user: User, answer_text: str) -> DailyPrompt:
    prompt = get_or_create_daily_prompt(db, user)

    answer_row = db.scalar(
        select(Answer).where(
            Answer.prompt_id == prompt.id,
            Answer.user_id == user.id,
        )
    )
    if answer_row is None:
        answer_row = Answer(prompt_id=prompt.id, user_id=user.id, body=answer_text.strip())
        db.add(answer_row)
    else:
        answer_row.body = answer_text.strip()

    db.commit()
    db.refresh(prompt)
    return prompt
