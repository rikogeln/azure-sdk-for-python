# coding=utf-8
# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------

from typing import Any, Optional, TYPE_CHECKING

from azure.mgmt.core import AsyncARMPipelineClient
from msrest import Deserializer, Serializer

if TYPE_CHECKING:
    # pylint: disable=unused-import,ungrouped-imports
    from azure.core.credentials_async import AsyncTokenCredential

from ._configuration import ConsumptionManagementClientConfiguration
from .operations import UsageDetailsOperations
from .operations import MarketplacesOperations
from .operations import BudgetsOperations
from .operations import TagsOperations
from .operations import ChargesOperations
from .operations import BalancesOperations
from .operations import ReservationsSummariesOperations
from .operations import ReservationsDetailsOperations
from .operations import ReservationRecommendationsOperations
from .operations import ReservationRecommendationDetailsOperations
from .operations import ReservationTransactionsOperations
from .operations import PriceSheetOperations
from .operations import ForecastsOperations
from .operations import Operations
from .operations import AggregatedCostOperations
from .operations import EventsOperations
from .operations import LotsOperations
from .operations import CreditsOperations
from .. import models


class ConsumptionManagementClient(object):
    """Consumption management client provides access to consumption resources for Azure Enterprise Subscriptions.

    :ivar usage_details: UsageDetailsOperations operations
    :vartype usage_details: azure.mgmt.consumption.aio.operations.UsageDetailsOperations
    :ivar marketplaces: MarketplacesOperations operations
    :vartype marketplaces: azure.mgmt.consumption.aio.operations.MarketplacesOperations
    :ivar budgets: BudgetsOperations operations
    :vartype budgets: azure.mgmt.consumption.aio.operations.BudgetsOperations
    :ivar tags: TagsOperations operations
    :vartype tags: azure.mgmt.consumption.aio.operations.TagsOperations
    :ivar charges: ChargesOperations operations
    :vartype charges: azure.mgmt.consumption.aio.operations.ChargesOperations
    :ivar balances: BalancesOperations operations
    :vartype balances: azure.mgmt.consumption.aio.operations.BalancesOperations
    :ivar reservations_summaries: ReservationsSummariesOperations operations
    :vartype reservations_summaries: azure.mgmt.consumption.aio.operations.ReservationsSummariesOperations
    :ivar reservations_details: ReservationsDetailsOperations operations
    :vartype reservations_details: azure.mgmt.consumption.aio.operations.ReservationsDetailsOperations
    :ivar reservation_recommendations: ReservationRecommendationsOperations operations
    :vartype reservation_recommendations: azure.mgmt.consumption.aio.operations.ReservationRecommendationsOperations
    :ivar reservation_recommendation_details: ReservationRecommendationDetailsOperations operations
    :vartype reservation_recommendation_details: azure.mgmt.consumption.aio.operations.ReservationRecommendationDetailsOperations
    :ivar reservation_transactions: ReservationTransactionsOperations operations
    :vartype reservation_transactions: azure.mgmt.consumption.aio.operations.ReservationTransactionsOperations
    :ivar price_sheet: PriceSheetOperations operations
    :vartype price_sheet: azure.mgmt.consumption.aio.operations.PriceSheetOperations
    :ivar forecasts: ForecastsOperations operations
    :vartype forecasts: azure.mgmt.consumption.aio.operations.ForecastsOperations
    :ivar operations: Operations operations
    :vartype operations: azure.mgmt.consumption.aio.operations.Operations
    :ivar aggregated_cost: AggregatedCostOperations operations
    :vartype aggregated_cost: azure.mgmt.consumption.aio.operations.AggregatedCostOperations
    :ivar events: EventsOperations operations
    :vartype events: azure.mgmt.consumption.aio.operations.EventsOperations
    :ivar lots: LotsOperations operations
    :vartype lots: azure.mgmt.consumption.aio.operations.LotsOperations
    :ivar credits: CreditsOperations operations
    :vartype credits: azure.mgmt.consumption.aio.operations.CreditsOperations
    :param credential: Credential needed for the client to connect to Azure.
    :type credential: ~azure.core.credentials_async.AsyncTokenCredential
    :param subscription_id: Azure Subscription ID.
    :type subscription_id: str
    :param str base_url: Service URL
    """

    def __init__(
        self,
        credential: "AsyncTokenCredential",
        subscription_id: str,
        base_url: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        if not base_url:
            base_url = 'https://management.azure.com'
        self._config = ConsumptionManagementClientConfiguration(credential, subscription_id, **kwargs)
        self._client = AsyncARMPipelineClient(base_url=base_url, config=self._config, **kwargs)

        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self._serialize = Serializer(client_models)
        self._serialize.client_side_validation = False
        self._deserialize = Deserializer(client_models)

        self.usage_details = UsageDetailsOperations(
            self._client, self._config, self._serialize, self._deserialize)
        self.marketplaces = MarketplacesOperations(
            self._client, self._config, self._serialize, self._deserialize)
        self.budgets = BudgetsOperations(
            self._client, self._config, self._serialize, self._deserialize)
        self.tags = TagsOperations(
            self._client, self._config, self._serialize, self._deserialize)
        self.charges = ChargesOperations(
            self._client, self._config, self._serialize, self._deserialize)
        self.balances = BalancesOperations(
            self._client, self._config, self._serialize, self._deserialize)
        self.reservations_summaries = ReservationsSummariesOperations(
            self._client, self._config, self._serialize, self._deserialize)
        self.reservations_details = ReservationsDetailsOperations(
            self._client, self._config, self._serialize, self._deserialize)
        self.reservation_recommendations = ReservationRecommendationsOperations(
            self._client, self._config, self._serialize, self._deserialize)
        self.reservation_recommendation_details = ReservationRecommendationDetailsOperations(
            self._client, self._config, self._serialize, self._deserialize)
        self.reservation_transactions = ReservationTransactionsOperations(
            self._client, self._config, self._serialize, self._deserialize)
        self.price_sheet = PriceSheetOperations(
            self._client, self._config, self._serialize, self._deserialize)
        self.forecasts = ForecastsOperations(
            self._client, self._config, self._serialize, self._deserialize)
        self.operations = Operations(
            self._client, self._config, self._serialize, self._deserialize)
        self.aggregated_cost = AggregatedCostOperations(
            self._client, self._config, self._serialize, self._deserialize)
        self.events = EventsOperations(
            self._client, self._config, self._serialize, self._deserialize)
        self.lots = LotsOperations(
            self._client, self._config, self._serialize, self._deserialize)
        self.credits = CreditsOperations(
            self._client, self._config, self._serialize, self._deserialize)

    async def close(self) -> None:
        await self._client.close()

    async def __aenter__(self) -> "ConsumptionManagementClient":
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *exc_details) -> None:
        await self._client.__aexit__(*exc_details)
