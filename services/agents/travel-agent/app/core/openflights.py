'''
Open flights
'''
import pandas as pd
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Column definitions ────────────────────────────────────────────────────────

AIRPORT_COLUMNS = [
    "id", "name", "city", "country", "iata", "icao",
    "latitude", "longitude", "altitude", "timezone",
    "dst", "tz_database", "type", "source"
]

ROUTE_COLUMNS = [
    "airline", "airline_id", "source_airport", "source_airport_id",
    "dest_airport", "dest_airport_id", "codeshare", "stops", "equipment"
]

AIRLINE_COLUMNS = [
    "id", "name", "alias", "iata", "icao",
    "callsign", "country", "active"
]


class OpenFlightsData:
    """
    Loads and queries the OpenFlights static dataset.
    Data is loaded once at startup and kept in memory for fast in-process querying.
    No external API calls are made at runtime.
    """

    def __init__(self):
        """Initialize empty dataframes — populated on load()."""
        self.airports: pd.DataFrame = pd.DataFrame()
        self.routes: pd.DataFrame = pd.DataFrame()
        self.airlines: pd.DataFrame = pd.DataFrame()
        self._loaded = False

    def load(self):
        """
        Load all three OpenFlights datasets from disk into pandas DataFrames.
        Called once during FastAPI lifespan startup.
        """
        try:
            self.airports = pd.read_csv(
                settings.AIRPORTS_DATA_PATH,
                header=None,
                names=AIRPORT_COLUMNS,
                na_values=["\\N", ""],
                encoding="utf-8"
            )
            # keep only real airports with valid IATA codes
            self.airports = self.airports[
                self.airports["iata"].notna() &
                (self.airports["iata"] != "\\N") &
                (self.airports["type"] == "airport")
            ].reset_index(drop=True)

            self.routes = pd.read_csv(
                settings.ROUTES_DATA_PATH,
                header=None,
                names=ROUTE_COLUMNS,
                na_values=["\\N", ""],
                encoding="utf-8"
            )

            self.airlines = pd.read_csv(
                settings.AIRLINES_DATA_PATH,
                header=None,
                names=AIRLINE_COLUMNS,
                na_values=["\\N", ""],
                encoding="utf-8"
            )
            # keep only active airlines with valid IATA codes
            self.airlines = self.airlines[
                self.airlines["active"] == "Y"
            ].reset_index(drop=True)

            self._loaded = True
            logger.info(
                "openflights_data_loaded",
                airports=len(self.airports),
                routes=len(self.routes),
                airlines=len(self.airlines)
            )

        except Exception as e:
            logger.error("openflights_load_failed", error=str(e))
            raise

    def is_loaded(self) -> bool:
        """Return True if datasets have been loaded successfully."""
        return self._loaded

    # ── Airport queries ───────────────────────────────────────────────────────

    def search_airports_by_city(self, city: str, limit: int = 10) -> list[dict]:
        """Search airports by city name (case-insensitive partial match)."""
        mask = self.airports["city"].str.contains(city, case=False, na=False)
        return self.airports[mask].head(limit).to_dict(orient="records")

    def search_airports_by_country(self, country: str, limit: int = 20) -> list[dict]:
        """Search airports by country name (case-insensitive partial match)."""
        mask = self.airports["country"].str.contains(country, case=False, na=False)
        return self.airports[mask].head(limit).to_dict(orient="records")

    def get_airport_by_iata(self, iata: str) -> dict | None:
        """Get a single airport by its IATA code (e.g. 'LHR', 'JFK')."""
        result = self.airports[
            self.airports["iata"].str.upper() == iata.upper()
        ]
        if result.empty:
            return None
        return result.iloc[0].to_dict()

    def search_airports(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search airports by name, city, IATA or country.
        Tries IATA exact match first, then falls back to name/city search.
        """
        # exact IATA match
        if len(query) == 3:
            exact = self.get_airport_by_iata(query)
            if exact:
                return [exact]

        # name or city partial match
        mask = (
            self.airports["name"].str.contains(query, case=False, na=False) |
            self.airports["city"].str.contains(query, case=False, na=False) |
            self.airports["country"].str.contains(query, case=False, na=False)
        )
        return self.airports[mask].head(limit).to_dict(orient="records")

    # ── Route queries ─────────────────────────────────────────────────────────

    def search_routes(
        self,
        source_iata: str,
        dest_iata: str,
        limit: int = 20
    ) -> list[dict]:
        """
        Find all routes between two airports by IATA code.
        Returns list of routes including airline and equipment info.
        """
        mask = (
            (self.routes["source_airport"].str.upper() == source_iata.upper()) &
            (self.routes["dest_airport"].str.upper() == dest_iata.upper())
        )
        return self.routes[mask].head(limit).to_dict(orient="records")

    def get_routes_from(self, source_iata: str, limit: int = 50) -> list[dict]:
        """Get all routes departing from a given airport."""
        mask = self.routes["source_airport"].str.upper() == source_iata.upper()
        return self.routes[mask].head(limit).to_dict(orient="records")

    def get_routes_to(self, dest_iata: str, limit: int = 50) -> list[dict]:
        """Get all routes arriving at a given airport."""
        mask = self.routes["dest_airport"].str.upper() == dest_iata.upper()
        return self.routes[mask].head(limit).to_dict(orient="records")

    # ── Airline queries ───────────────────────────────────────────────────────

    def search_airlines(self, query: str, limit: int = 10) -> list[dict]:
        """Search airlines by name, IATA or country (case-insensitive)."""
        mask = (
            self.airlines["name"].str.contains(query, case=False, na=False) |
            self.airlines["iata"].str.contains(query, case=False, na=False) |
            self.airlines["country"].str.contains(query, case=False, na=False)
        )
        return self.airlines[mask].head(limit).to_dict(orient="records")

    def get_airline_by_iata(self, iata: str) -> dict | None:
        """Get a single airline by its IATA code (e.g. 'BA', 'QR')."""
        result = self.airlines[
            self.airlines["iata"].str.upper() == iata.upper()
        ]
        if result.empty:
            return None
        return result.iloc[0].to_dict()

    def get_airlines_by_country(self, country: str, limit: int = 20) -> list[dict]:
        """Get all active airlines from a given country."""
        mask = self.airlines["country"].str.contains(country, case=False, na=False)
        return self.airlines[mask].head(limit).to_dict(orient="records")


# ── Alternative: live API clients ─────────────────────────────────────────────
# When a live API becomes accessible, replace this class with:
#
# Amadeus:
#   from amadeus import Client
#   client = Client(client_id=settings.AMADEUS_API_KEY, client_secret=settings.AMADEUS_SECRET)
#   results = client.shopping.flight_offers_search.get(
#       originLocationCode="LHR", destinationLocationCode="JFK",
#       departureDate="2026-07-01", adults=1
#   )
#
# Aviationstack:
#   params = {"access_key": settings.AVIATIONSTACK_KEY, "dep_iata": "LHR", "arr_iata": "JFK"}
#   response = await client.get("http://api.aviationstack.com/v1/flights", params=params)
# ─────────────────────────────────────────────────────────────────────────────

openflights_data = OpenFlightsData()
