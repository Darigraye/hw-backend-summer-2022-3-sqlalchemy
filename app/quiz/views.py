from aiohttp.web_exceptions import HTTPConflict, HTTPUnauthorized, HTTPForbidden, HTTPBadRequest, HTTPNotFound
from aiohttp_apispec import querystring_schema, request_schema, response_schema
from aiohttp_session import get_session

from app.quiz.models import Answer
from app.quiz.schemes import (
    ListQuestionSchema,
    QuestionSchema,
    ThemeIdSchema,
    ThemeListSchema,
    ThemeSchema,
)
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class ThemeAddView(AuthRequiredMixin, View):
    @request_schema(ThemeSchema)
    @response_schema(ThemeSchema)
    async def post(self):
        await super()._check_user_authorization()
        await super()._check_correct_user_email()

        title = self.data['title']
        theme = await self.store.quizzes.get_theme_by_title(title)

        if theme:
            raise HTTPConflict
        else:
            theme = await self.store.quizzes.create_theme(title=title)
            return json_response(data=ThemeSchema().dump(theme))


class ThemeListView(AuthRequiredMixin, View):
    @response_schema(ThemeListSchema)
    async def get(self):
        await super()._check_user_authorization()
        await super()._check_correct_user_email()

        themes = await self.store.quizzes.list_themes()
        return json_response(data={'themes': [ThemeSchema().dump(theme) for theme in themes]})


class QuestionAddView(AuthRequiredMixin, View):
    @classmethod
    async def _answers_are_correct(cls, answers) -> bool:
        one_answer_true = False
        result = True

        if len(answers) == 1:
            result = False
        else:
            for answer in answers:
                if answer['is_correct']:
                    if one_answer_true:
                        result = False
                        break
                    one_answer_true = True

        return result and one_answer_true

    @request_schema(QuestionSchema)
    @response_schema(QuestionSchema)
    async def post(self):
        await super()._check_user_authorization()
        await super()._check_correct_user_email()

        title = self.data['title']
        theme_id = self.data['theme_id']
        answers = self.data['answers']

        if not await self._answers_are_correct(answers):
            raise HTTPBadRequest

        if not await self.store.quizzes.get_theme_by_id(theme_id):
            raise HTTPNotFound

        if await self.store.quizzes.get_question_by_title(title):
            raise HTTPConflict

        question = await self.store.quizzes.create_question(title, theme_id, [
            Answer(title=answer['title'],
                   is_correct=answer['is_correct']
                   )
            for answer in answers])

        return json_response(data=({'id': question.id} | self.data))


class QuestionListView(AuthRequiredMixin, View):
    @querystring_schema(ThemeIdSchema)
    @response_schema(ListQuestionSchema)
    async def get(self):
        await super()._check_user_authorization()
        await super()._check_correct_user_email()

        theme_id = self.request.query.get('theme_id')
        questions = await self.store.quizzes.list_questions(theme_id)

        return json_response(data={'questions': [QuestionSchema().dump(question) for question in questions]})
