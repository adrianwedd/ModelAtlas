import nest_asyncio


def pytest_sessionstart(session):
    nest_asyncio.apply()
