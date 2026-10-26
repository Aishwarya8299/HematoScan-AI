"""MongoDB collection names and index definitions."""

from pymongo import ASCENDING, DESCENDING, IndexModel

USERS_COLLECTION = "users"
CASES_COLLECTION = "cases"
REVOKED_TOKENS_COLLECTION = "revoked_tokens"

USER_EMAIL_FIELD = "email"

INDEXES: dict[str, list[IndexModel]] = {
    USERS_COLLECTION: [
        IndexModel([("email", ASCENDING)], unique=True, name="unique_email"),
        IndexModel([("role", ASCENDING)], name="role_lookup"),
    ],
    CASES_COLLECTION: [
        IndexModel(
            [("status", ASCENDING), ("priority", DESCENDING), ("created_at", DESCENDING)],
            name="queue_priority",
        ),
        IndexModel([("patient_id", ASCENDING)], name="patient_lookup"),
        IndexModel([("created_by", ASCENDING)], name="creator_lookup"),
    ],
    REVOKED_TOKENS_COLLECTION: [
        IndexModel([("token_id", ASCENDING)], unique=True, name="unique_token_id"),
        IndexModel(
            [("expires_at", ASCENDING)],
            expireAfterSeconds=0,
            name="revoked_token_expiry",
        ),
    ],
}
