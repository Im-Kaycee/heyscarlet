# HeyScarlet Progress

This file tracks the current implementation state so future work can pick up from the same point without re-reading the whole repo.

## Completed

- Added [`app/core/dependencies.py`](/home/varane/heyscarlet/app/core/dependencies.py) with `get_current_user`.
- `get_current_user` reads the `Authorization` header, validates the `Bearer` token, decodes the JWT with `decode_access_token`, looks up the user in the database, and returns the `User` object.
- Wired [`app/api/routes/auth.py`](/home/varane/heyscarlet/app/api/routes/auth.py) `/auth/me` to `Depends(get_current_user)`.

## Pending

- Wire `get_current_user` into [`app/api/routes/chat.py`](/home/varane/heyscarlet/app/api/routes/chat.py).
- Replace the temporary hardcoded user ID in the chat stream route.
- Implement the stubbed conversation endpoints in the chat router.
- Add tests for auth and chat flows once the remaining wiring is in place.

## Notes

- The JWT `sub` claim is treated as the user UUID.
- `/auth/me` now returns the authenticated `User` instance directly through the route response model.
- The chat route still uses temporary user wiring until auth dependency integration is approved.
