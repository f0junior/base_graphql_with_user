import strawberry

from app.graphql.mutations.user_mutation import UserMutation


@strawberry.type
class Mutation(UserMutation):
    pass
