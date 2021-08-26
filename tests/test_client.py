import unittest

import pandas as pd
from lxml import etree
from pandas import DataFrame

from entsoe_client import Client
from entsoe_client import Parser
from entsoe_client import Queries
from entsoe_client.ParameterTypes import *
from settings import *


class ParameterTypeTest(unittest.TestCase):
    def test_types(self):
        self.assertIsInstance(Area.DE_TENNET, Area)
        self.assertIsInstance(AuctionCategory.A01, AuctionCategory)
        self.assertIsInstance(AuctionType.A01, AuctionType)
        self.assertIsInstance(BusinessType.B01, BusinessType)
        self.assertIsInstance(DocStatus.A01, DocStatus)
        self.assertIsInstance(DocumentType.A85, DocumentType)
        self.assertIsInstance(MarketAgreementType.A01, MarketAgreementType)
        self.assertIsInstance(ProcessType.A01, ProcessType)
        self.assertIsInstance(PsrType.B01, PsrType)


class QueryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.q1 = Queries.Load.ActualTotalLoad(
            Area.CZ,
            '201512312300',
            '201612312300')
        cls.q2 = Queries.Transmission.ExpansionDismantlingProjects(
            in_Domain=Area.SE_3, out_Domain=Area.SE_4,
            periodStart='201412312300', periodEnd='201512312300',
            businessType=BusinessType.B01)
        cls.q3 = Queries.Transmission.ForecastedCapacity(
            marketAgreementType=MarketAgreementType.A01,
            in_Domain=Area.CZ, out_Domain=Area.SK,
            periodStart='201512312300', periodEnd='201612312300')
        cls.q4 = Queries.Transmission.FlowbasedParameters(
            processType=ProcessType.A01, in_Domain=Area.CWE, out_Domain=Area.CWE,
            periodStart='201512312300', periodEnd='201601012300')
        cls.q5 = Queries.Transmission.IntradayTransferLimits(
            in_Domain=Area.GB, out_Domain=Area.FR,
            periodStart='201512312300', periodEnd='201601312300')
        cls.q6 = Queries.Transmission.ExplicitAllocationInformationRevenueonly(
            contract_MarketAgreementType=MarketAgreementType.A01,
            in_Domain=Area.AT, out_Domain=Area.CZ,
            periodStart='201601012300', periodEnd='201601022300')

    def test_init_fail(self):
        with self.assertRaises(TypeError):
            Queries.Load.ActualTotalLoad()

    def test_init_success(self):
        q = Queries.Load.ActualTotalLoad(Area.CZ, '201512312300', '201612312300')
        params = {'documentType': 'A65', 'processType': 'A16', 'outBiddingZone_Domain': '10YCZ-CEPS-----N',
                  'periodStart': '201512312300', 'periodEnd': '201612312300'}
        self.assertIsInstance(q, Queries.Query)
        self.assertIsInstance(q(), dict)
        self.assertEqual(q(), q() | params)

    def test_call(self):
        query_params = dict((k, v) for (k, v) in self.q2().items() if v)
        query_params.pop('documentType', None)
        actual_params = dict(in_Domain=Area.SE_3.code, out_Domain=Area.SE_4.code,
                             periodStart='201412312300', periodEnd='201512312300',
                             businessType=BusinessType.B01.name)
        self.assertEqual(query_params, actual_params)


class ParserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        mock_period_str = \
            b'<Period xmlns="urn:iec62325.351:tc57wg16:451-6:balancingdocument:3:0">\n\t\t\t<timeInterval>\n\t\t\t\t<start>2018-02-28T23:45Z</start>\n\t\t\t\t<end>2018-03-01T00:00Z</end>\n\t\t\t</timeInterval>\n\t\t\t<resolution>PT15M</resolution>\n\t\t\t<Point>\n\t\t\t\t<position>1</position>\n\t\t\t\t<quantity>11</quantity>\n\t\t\t</Point>\n\t\t</Period>\n\t\t'
        cls.mock_period = etree.fromstring(mock_period_str)

    def test_period_to_dataframe(self):
        df = Parser.utils.Period_to_DataFrame(self.mock_period)
        self.assertIsInstance(df, pd.DataFrame)


class IntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.queries = [
            Queries.Load.ActualTotalLoad(
                Area.CZ,
                '201512312300',
                '201612312300'),
            Queries.Transmission.ExpansionDismantlingProjects(
                in_Domain=Area.SE_3, out_Domain=Area.SE_4,
                periodStart='201412312300', periodEnd='201512312300',
                businessType=BusinessType.B01),
            Queries.Transmission.ForecastedCapacity(
                marketAgreementType=MarketAgreementType.A01,
                in_Domain=Area.CZ, out_Domain=Area.SK,
                periodStart='201512312300', periodEnd='201612312300'),
            Queries.Transmission.FlowbasedParameters(
                processType=ProcessType.A01, in_Domain=Area.CWE, out_Domain=Area.CWE,
                periodStart='201512312300', periodEnd='201601012300'),
            Queries.Transmission.IntradayTransferLimits(
                in_Domain=Area.GB, out_Domain=Area.FR,
                periodStart='201512312300', periodEnd='201601312300'),
            Queries.Transmission.ExplicitAllocationInformationRevenueonly(
                contract_MarketAgreementType=MarketAgreementType.A01,
                in_Domain=Area.AT, out_Domain=Area.CZ,
                periodStart='201601012300', periodEnd='201601022300'),
            Queries.Query(
                documentType=DocumentType.A85, controlArea_Domain=Area.BE,
                periodStart='202001010100', periodEnd='202007010000'),
            Queries.Query(
                documentType=DocumentType.A86, controlArea_Domain=Area.BE,
                periodStart='202108220000', periodEnd='202108221200'),
            Queries.Query(
                documentType=DocumentType.A86, businessType=BusinessType.B33, Area_Domain=Area.CZ,
                periodStart='202108220000', periodEnd='202108221200')
        ]

    def test_integration(self):
        client = Client(api_key=api_key)
        self.assertIsInstance(client, Client)

        query = self.queries[0]
        self.assertIsInstance(query, Queries.Query)

        response = client.download(query)
        self.assertTrue(response.ok)

        df = Parser.parse(response)
        self.assertIsInstance(df, DataFrame)

    def test_all(self):
        client = Client(api_key=api_key)
        for query in self.queries:
            with self.subTest(type(query).__name__):
                response = client.download(query)
                df = Parser.parse(response)
                self.assertIsInstance(df, DataFrame)


if __name__ == '__main__':
    unittest.main(verbosity=101)
