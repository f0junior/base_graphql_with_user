from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.redis import redis_manager
from app.core.settings import settings
from app.graphql.context_getter import get_context
from app.graphql.custom_graphql_route import CustomGraphQLRouter
from app.graphql.schema import schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🔌 Aplicação iniciando...")
    async with redis_manager.lifespan():
        yield
    print("🔌 Aplicação encerrando...")


app = FastAPI(title=settings.dbname, lifespan=lifespan)

graphql_app = CustomGraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")
