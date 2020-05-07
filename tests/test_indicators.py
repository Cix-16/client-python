# coding: utf-8

import json
from dateutil.parser import parse
from pycti import OpenCTIApiClient
from stix2 import TLP_AMBER, TLP_GREEN

import pytest


@pytest.fixture
def api_client():
    return OpenCTIApiClient(
        "https://demo.opencti.io",
        "2b4f29e3-5ea8-4890-8cf5-a76f61f1e2b2",
        ssl_verify=True,
    )


@pytest.fixture
def test_indicator(api_client):
    # Define the date
    date = parse("2019-12-01").strftime("%Y-%m-%dT%H:%M:%SZ")
    date2 = parse("2021-12-01").strftime("%Y-%m-%dT%H:%M:%SZ")

    # Create the organization
    organization = api_client.identity.create(
        type="Organization", name="Testing Inc.", description="OpenCTI Test Org"
    )
    return api_client.indicator.create(
        name="C2 server of the new campaign",
        description="This is the C2 server of the campaign",
        pattern_type="stix",
        indicator_pattern="[domain-name:value = 'www.5z8.info' AND domain-name:resolves_to_refs[*].value = '198.51.100.1/32']",
        main_observable_type="IPv4-Addr",
        confidence=60,
        score=80,
        detection=True,
        valid_from=date,
        valid_until=date2,
        created=date,
        modified=date,
        tags=["Test1", "Test2"],
        createdByRef=organization["id"],
        markingDefinitions=[TLP_AMBER["id"], TLP_GREEN["id"]],
        update=True,
        # TODO: killChainPhases
    )


def test_create_indicator(test_indicator):
    assert test_indicator["id"] is not None or test_indicator["id"] != ""


def test_read_indicator_by_id(api_client, test_indicator):
    indicator = api_client.indicator.read(id=test_indicator["id"])
    assert indicator["id"] is not None or indicator["id"] != ""
    assert indicator["id"] == test_indicator["id"]


def test_read_indicator_by_filter(api_client, test_indicator):
    indicator2 = api_client.indicator.read(
        filters=[{"key": "name", "values": [test_indicator["name"]], "operator": "eq",}]
    )
    assert indicator2["id"] is not None or indicator2["id"] != ""
    assert indicator2["id"] == test_indicator["id"]


def test_get_100_indicators_with_pagination(api_client):
    # Get all reports using the pagination
    custom_attributes = """
        id
        indicator_pattern
        created
    """

    final_indicators = []
    data = api_client.indicator.list(
        first=50, customAttributes=custom_attributes, withPagination=True
    )
    final_indicators = final_indicators + data["entities"]

    assert len(final_indicators) == 50

    after = data["pagination"]["endCursor"]
    data = api_client.indicator.list(
        first=50, after=after, customAttributes=custom_attributes, withPagination=True,
    )
    final_indicators = final_indicators + data["entities"]

    assert len(final_indicators) == 100


def test_add_stix_observable_to_indicator(api_client, test_indicator):
    observable_ttp1 = api_client.stix_observable.create(
        type="Email-Address", observable_value="phishing@mail.com",
    )

    assert api_client.indicator.add_stix_observable(
        id=test_indicator["id"], stix_observable_id=observable_ttp1["id"]
    )


def test_indicator_stix_marshall(api_client, test_indicator):
    stix_indicator = api_client.indicator.to_stix2(id=test_indicator["id"], mode="full")
    assert stix_indicator is not None

    with open("tests/testdata/indicator_stix.json", "r") as content_file:
        content = content_file.read()

    json_data = json.loads(content)

    for indic in json_data["objects"]:
        imported_indicator = api_client.indicator.import_from_stix2(
            stixObject=indic, update=True
        )
        assert imported_indicator is not None
