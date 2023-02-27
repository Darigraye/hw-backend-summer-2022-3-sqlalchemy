from aiohttp.abc import StreamResponse
from aiohttp.web_exceptions import HTTPUnauthorized, HTTPForbidden
from aiohttp_session import get_session


class AuthRequiredMixin:
    async def _iter(self) -> StreamResponse:
        if not getattr(self.request, "admin", None):
            raise HTTPUnauthorized
        return await super(AuthRequiredMixin, self)._iter()

    async def _check_user_authorization(self):
        session = await get_session(self.request)
        if session is None:
            raise HTTPUnauthorized

    async def _check_correct_user_email(self):
        session = await get_session(self.request)
        user = await self.store.admins.get_by_email(session['admin']['email'])
        if not user or session['admin']['email'] != user.email:
            raise HTTPForbidden
