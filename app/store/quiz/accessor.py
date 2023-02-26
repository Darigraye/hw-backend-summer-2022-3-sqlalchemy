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
    async def create_theme(self, title: str) -> Theme:
        async with self.app.database.session() as session:
            session.add(ThemeModel(
                title=title
            ))
            await session.commit()
            res = await session.execute(
                select(ThemeModel).where(ThemeModel.title == title)
            )
            raw_res = res.scalars().all()
            await session.commit()
        return Theme(
            id=raw_res[0].id,
            title=raw_res[0].title
        )

    async def get_theme_by_title(self, title: str) -> Theme | None:
        query = select(ThemeModel).where(ThemeModel.title == title)
        async with self.app.database.session.begin() as session:
            res = await session.execute(query)
            raw_res = res.scalars().all()
            await session.commit()
        if len(raw_res) != 0:
            return Theme(
                id=raw_res[0].id,
                title=raw_res[0].title
            )

    async def get_theme_by_id(self, id_: int) -> Theme | None:
        query = select(ThemeModel).where(ThemeModel.id == id_)
        async with self.app.database.session.begin() as session:
            res = await session.execute(query)
            raw_res = res.scalars().all()
            await session.commit()
        if len(raw_res) != 0:
            return Theme(
                id=raw_res[0].id,
                title=raw_res[0].title
            )

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
            for answer in answers:
                ans = AnswerModel(
                    title=answer.title,
                    is_correct=answer.is_correct,
                    question_id=question_id
                )
                session.add(ans)
                await session.commit()
        return answers

    async def create_question(
            self, title: str, theme_id: int, answers: list[Answer]
    ) -> Question:
        question = QuestionModel(
                title=title,
                theme_id=theme_id
            )
        async with self.app.database.session() as session:
            session.add(question)
            await session.commit()
            await session.refresh(question)
            raw_answers = await self.create_answers(question.id, answers)
        return Question(
            id=question.id,
            theme_id=question.theme_id,
            title=question.title,
            answers=raw_answers
        )

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
            wrapped_data = res.scalars().all()
            await session.commit()
            if len(wrapped_data):
                serialized_answers = await self._serialize_answers(wrapped_data[0].answers)
                return Question(id=wrapped_data[0].id, title=wrapped_data.title,
                                theme_id=wrapped_data[0].theme_id,
                                answers=serialized_answers)

    async def list_questions(self, theme_id: int | None = None) -> list[Question]:
        if not theme_id:
            query = select(QuestionModel)
        else:
            query = select(QuestionModel).where(QuestionModel.theme_id == int(theme_id))
        questions = []
        async with self.app.database.session.begin() as session:
            res = await session.execute(query)
            raw_res_q = res.scalars().all()
            await session.commit()
        for raw_q in raw_res_q:
            raw_answers = []
            query = select(AnswerModel).where(AnswerModel.question_id == raw_q.id)
            async with self.app.database.session.begin() as session:
                res = await session.execute(query)
                raw_res_a = res.scalars().all()
                await session.commit()
            for raw_a in raw_res_a:
                raw_answers += [Answer(
                    title=raw_a.title,
                    is_correct=raw_a.is_correct
                )]
            questions += [Question(
                id=raw_q.id,
                title=raw_q.title,
                theme_id=raw_q.theme_id,
                answers=raw_answers
            )]
        return questions
