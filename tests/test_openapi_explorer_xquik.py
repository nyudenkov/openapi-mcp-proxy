import unittest

from openapi_mcp_proxy.models.pagination import EndpointFilterParams
from openapi_mcp_proxy.services.openapi_explorer import OpenAPIExplorer


XQUIK_SCHEMA = {
    "openapi": "3.1.0",
    "info": {"title": "Xquik API", "version": "1.0"},
    "servers": [{"url": "https://xquik.com"}],
    "security": [{"apiKey": []}],
    "components": {
        "securitySchemes": {
            "apiKey": {
                "type": "apiKey",
                "in": "header",
                "name": "x-api-key",
            }
        },
        "schemas": {
            "PaginatedTweets": {
                "type": "object",
                "properties": {
                    "tweets": {"type": "array"},
                    "next_cursor": {"type": "string"},
                },
                "required": ["tweets"],
            }
        },
    },
    "paths": {
        "/api/v1/x/tweets/search": {
            "get": {
                "operationId": "searchTweets",
                "summary": "Search tweets by query, Tweet ID, X status URL, or account date window",
                "tags": ["Tweets"],
                "parameters": [
                    {
                        "name": "q",
                        "in": "query",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Search results",
                    }
                },
            }
        }
    },
}


class StubConfigManager:
    def get_api_config(self, api_identifier):
        self.api_identifier = api_identifier
        return "https://xquik.com/openapi.json", {"x-api-key": "test"}


class StubOpenAPICache:
    async def get_schema(self, url, headers):
        self.url = url
        self.headers = headers
        return XQUIK_SCHEMA


class OpenAPIExplorerXquikSchemaTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.config_manager = StubConfigManager()
        self.cache = StubOpenAPICache()
        self.explorer = OpenAPIExplorer(self.config_manager, self.cache)

    async def test_reports_api_info_from_openapi31_schema(self):
        api_info = await self.explorer.get_api_info("xquik")

        self.assertEqual(api_info.title, "Xquik API")
        self.assertEqual(api_info.version, "1.0")
        self.assertEqual(api_info.base_url, "https://xquik.com")

    async def test_lists_and_filters_authenticated_search_endpoint(self):
        endpoints = await self.explorer.list_endpoints("xquik")

        self.assertEqual(len(endpoints), 1)
        endpoint = endpoints[0]
        self.assertEqual(endpoint.path, "/api/v1/x/tweets/search")
        self.assertEqual(endpoint.method, "GET")
        self.assertEqual(endpoint.operation_id, "searchTweets")
        self.assertTrue(endpoint.has_authentication)

        filtered = self.explorer.filter_endpoints(
            endpoints,
            EndpointFilterParams(has_authentication=True, tags_include=["Tweets"]),
        )
        self.assertEqual(filtered, [endpoint])

    async def test_gets_endpoint_details_and_models(self):
        details = await self.explorer.get_endpoint_details(
            "xquik",
            "/api/v1/x/tweets/search",
            "GET",
        )
        models = await self.explorer.list_models("xquik")

        self.assertEqual(details["operation_id"], "searchTweets")
        self.assertEqual(details["parameters"][0]["name"], "q")
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].name, "PaginatedTweets")
