import aiohttp_session
from aiohttp.web import HTTPForbidden, HTTPUnauthorized
from aiohttp_apispec import request_schema, response_schema
from aiohttp_session import new_session, get_session

from app.admin.schemes import AdminSchema
from app.web.app import View
from app.web.utils import json_response


class AdminLoginView(View):
    @request_schema(AdminSchema)
    @response_schema(AdminSchema, 200)
    async def post(self):
        data = self.data
        if admin := await self.store.admins.get_by_email(data['email']):
            if admin.is_password_valid(data['password']):
                session = await new_session(request=self.request)
                session['admin'] = dict()
                session['admin']['id'] = admin.id
                session['admin']['email'] = admin.email

                return json_response(data={'id': admin.id, 'email': admin.email})
        raise HTTPForbidden


class AdminCurrentView(View):
    @response_schema(AdminSchema, 200)
    async def get(self):
        if session := await get_session(self.request):
            admin = self.store.admins.get_by_email(session['admin']['email'])
            return json_response(data={'id': admin.id, 'email': admin.email})
        else:
            raise HTTPUnauthorized
