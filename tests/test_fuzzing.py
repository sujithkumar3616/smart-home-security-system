from hypothesis import given, settings, strategies as st

from app import create_app, db
from app.models.user import User, UserRole


def create_test_app():
    """Create a fresh testing application and database."""

    app = create_app("testing")

    with app.app_context():
        db.create_all()

        user = User(
            username="fuzzuser",
            role=UserRole.HOMEOWNER
        )
        user.set_password("FuzzTest#2026")

        db.session.add(user)
        db.session.commit()

    return app


# =========================================================
# FUZZ TEST 1 - LOGIN INPUT
# =========================================================

@given(
    username=st.text(min_size=0, max_size=100),
    password=st.text(min_size=0, max_size=100)
)
@settings(
    max_examples=50,
    deadline=None
)
def test_fuzz_login_payloads(username, password):

    app = create_test_app()

    try:
        with app.test_client() as client:

            response = client.post(
                "/api/login",
                json={
                    "username": username,
                    "password": password
                }
            )

        # Server must never crash.
        assert response.status_code != 500

        # Only valid test credentials should authenticate.
        if username == "fuzzuser" and password == "FuzzTest#2026":
            assert response.status_code == 200
        else:
            assert response.status_code in (400, 401, 422)

    finally:
        with app.app_context():
            db.session.remove()
            db.drop_all()


# =========================================================
# FUZZ TEST 2 - SENSOR EVENT INPUT
# =========================================================

@given(
    device_id=st.one_of(
        st.integers(min_value=-100000, max_value=100000),
        st.text(max_size=100)
    ),
    sensor_type=st.text(max_size=100),
    value=st.one_of(
        st.none(),
        st.integers(min_value=-100000, max_value=100000),
        st.floats(
            allow_nan=False,
            allow_infinity=False,
            width=32
        ),
        st.text(max_size=100)
    )
)
@settings(
    max_examples=50,
    deadline=None
)
def test_fuzz_sensor_events(device_id, sensor_type, value):

    app = create_test_app()

    try:
        with app.test_client() as client:

            response = client.post(
                "/api/sensors/event",
                json={
                    "device_id": device_id,
                    "sensor_type": sensor_type,
                    "value": value
                }
            )

        # Malformed input must never crash the server.
        assert response.status_code != 500

        # Endpoint requires authentication/device authorization.
        assert response.status_code in (
            400,
            401,
            403,
            404,
            422
        )

    finally:
        with app.app_context():
            db.session.remove()
            db.drop_all()


# =========================================================
# FUZZ TEST 3 - DEVICE COMMAND INPUT
# =========================================================

@given(
    device_id=st.one_of(
        st.integers(min_value=-100000, max_value=100000),
        st.from_regex(r"[A-Za-z0-9_-]{0,50}", fullmatch=True)
    ),
    command=st.text(max_size=100)
)
@settings(
    max_examples=50,
    deadline=None
)
def test_fuzz_device_commands(device_id, command):

    app = create_test_app()

    try:
        with app.test_client() as client:

            response = client.post(
                f"/api/devices/{device_id}/command",
                json={
                    "command": command
                }
            )

        # Fuzzed input must never crash the server.
        assert response.status_code != 500

        # Expected safe responses.
        assert response.status_code in (
            400,
            401,
            403,
            404,
            405,
            422
        )

    finally:
        with app.app_context():
            db.session.remove()
            db.drop_all()