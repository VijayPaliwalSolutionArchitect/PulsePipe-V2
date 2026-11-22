"""HTTP routers for the PulsePipe API.

Every router exposes an ``APIRouter``; the app entrypoint
(``backend/main.py``) imports them and includes each under the ``/api``
prefix.  Keeping a router per domain keeps the API surface discoverable and
matches the service modules one-to-one.
"""