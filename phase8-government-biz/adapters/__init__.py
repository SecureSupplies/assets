from .samples import SampleAdapter
from .sam_opportunities import SamOpportunitiesAdapter
from .usaspending import UsaSpendingAdapter
from .gsa_auctions import GsaAuctionsAdapter
from .eia import EiaAdapter
from .nws import NwsAdapter
from .openfema import OpenFemaAdapter
from .state_portals import StatePortalRegistryAdapter

ADAPTERS = [SamOpportunitiesAdapter, UsaSpendingAdapter, GsaAuctionsAdapter, EiaAdapter, NwsAdapter, OpenFemaAdapter, StatePortalRegistryAdapter]
TEST_ADAPTERS = [SampleAdapter]
