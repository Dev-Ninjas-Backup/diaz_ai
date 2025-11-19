from fastapi.openapi.utils import get_openapi


def custom_openapi(app):
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Ensure filters object shows all fields in examples
    if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
        if "SearchRequest" in openapi_schema["components"]["schemas"]:
            schema = openapi_schema["components"]["schemas"]["SearchRequest"]
            if "example" in schema:
                schema["example"] = {
                    "query": None,
                    "filters": {
                        "boat_type": None,
                        "make": None,
                        "model": None,
                        "build_year_min": None,
                        "build_year_max": None,
                        "price_min": None,
                        "price_max": None,
                        "length_min": None,
                        "length_max": None,
                        "beam_min": None,
                        "beam_max": None,
                        "number_of_engine": None,
                        "number_of_cabin": None,
                        "number_of_heads": None,
                        "additional_unit": None
                    }
                }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema
