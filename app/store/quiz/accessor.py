from sqlalchemy import insert, select

from app.base.base_accessor import BaseAccessor
from app.quiz.models import (
    Answer,
    Question,
    Theme,
    AnswerModel,
    QuestionModel,
    ThemeModel
)


class QuizAccessor(BaseAccessor):
    async def _get_wrapped_theme_by_title(self, title: str) -> ThemeModel | None:
        query = select(ThemeModel).where(ThemeModel.title == title)
        async with self.app.database.session.begin() as session:
            res = await session.execute(query)
            wrapped_theme = res.scalars().first()
            await session.commit()
        return wrapped_theme

    async def create_theme(self, title: str) -> Theme:
        async with self.app.database.session() as session:
            session.add(ThemeModel(title=title))
            await session.commit()

        wrapped_theme = await self._get_wrapped_theme_by_title(title)
        return Theme(
            id=wrapped_theme.id,
            title=wrapped_theme.title
        )

    async def get_theme_by_title(self, title: str) -> Theme | None:
        wrapped_theme = await self._get_wrapped_theme_by_title(title)
        if wrapped_theme is not None:
            return Theme(id=wrapped_theme.id, title=wrapped_theme.title)

    async def get_theme_by_id(self, id_: int) -> Theme | None:
        query_get_by_id = select(ThemeModel).where(ThemeModel.id == id_)
        async with self.app.database.session.begin() as session:
            res = await session.execute(query_get_by_id)
            wrapped_theme = res.scalars().first()
            await session.commit()
        if wrapped_theme is not None:
            return Theme(id=wrapped_theme.id, title=wrapped_theme.title)

    async def list_themes(self) -> list[Theme]:
        async with self.app.database.session.begin() as session:
            Q = select(ThemeModel)
            res = await session.execute(Q)
            wrapped_data = res.scalars().all()
            await session.commit()
        return [Theme(id=data.id, title=data.title) for data in wrapped_data]

    async def create_answers(
            self, question_id: int, answers: list[Answer]
    ) -> list[Answer]:
        async with self.app.database.session() as session:
            answer_models = [
                AnswerModel(
                    title=answer.title,
                    is_correct=answer.is_correct,
                    question_id=question_id
                ) for answer in answers
            ]
            session.add_all(answer_models)
            await session.commit()
        return answers

    async def create_question(
            self, title: str, theme_id: int, answers: list[Answer]
    ) -> Question:
        question = QuestionModel(title=title, theme_id=theme_id)
        async with self.app.database.session() as session:
            session.add(question)
            await session.commit()
            await session.refresh(question)

            wrapped_answers = await self.create_answers(question.id, answers)
        return Question(id=question.id, theme_id=question.theme_id, title=question.title, answers=wrapped_answers)

    @classmethod
    async def _serialize_answer(cls, answer: AnswerModel) -> Answer:
        return Answer(title=answer.title, is_correct=answer.is_correct)

    @classmethod
    async def _serialize_answers(cls, list_answers: list[AnswerModel]) -> list[Answer]:
        return [await cls._serialize_answer(answer) for answer in list_answers]

    async def get_question_by_title(self, title: str) -> Question | None:
        async with self.app.database.session() as session:
            Q = select(QuestionModel).where(QuestionModel.title == title)
            res = await session.execute(Q)
            wrapped_question = res.scalars().first()
            await session.commit()

            if wrapped_question is not None:
                query = select(AnswerModel).where(AnswerModel.question_id == wrapped_question.id)
                res = await session.execute(query)
                wrapped_answers = res.scalars().all()
                await session.commit()

                question = Question(
                    id=wrapped_question.id,
                    title=wrapped_question.title,
                    theme_id=wrapped_question.theme_id,
                    answers=await self._serialize_answers(wrapped_answers)
                )
                return question

    async def list_questions(self, theme_id: int | None = None) -> list[Question]:
        if theme_id is None:
            query_get_questions = select(QuestionModel)
        else:
            query_get_questions = select(QuestionModel).where(QuestionModel.theme_id == int(theme_id))

        questions = list()
        async with self.app.database.session.begin() as session:
            res = await session.execute(query_get_questions)
            wrapped_questions = res.scalars().all()
            await session.commit()

        for question in wrapped_questions:
            query_get_answer_by_id = select(AnswerModel).where(AnswerModel.question_id == question.id)
            async with self.app.database.session.begin() as session:
                res = await session.execute(query_get_answer_by_id)
                wrapped_answers = res.scalars().all()
                await session.commit()

            questions += [Question(
                id=question.id,
                title=question.title,
                theme_id=question.theme_id,
                answers=await self._serialize_answers(wrapped_answers)
            )]
        return questions
