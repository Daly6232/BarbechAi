def test_app_builds_without_import_errors():
    """Imports app.main and constructs the FastAPI app — the exact chain
    that failed in production (main.py -> app.api.crm -> app.services.
    crm_pipeline, missing `get_pipeline`). This test alone would have
    caught that incident before it ever reached a deploy."""
    import app.main as main_module
    assert main_module.app is not None


def test_all_routes_registered():
    import app.main as main_module
    paths = {route.path for route in main_module.app.routes}
    # Spot-check a handful of core endpoints exist, both legacy and versioned.
    for expected in ["/crm/pipeline", "/crm/leads", "/auth/login", "/health"]:
        assert expected in paths, f"{expected} missing from registered routes"
    for expected in ["/api/v1/crm/pipeline", "/api/v1/auth/login"]:
        assert expected in paths, f"{expected} missing from versioned routes"
