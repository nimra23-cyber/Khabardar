"""Repository layer: parameterized SQLAlchemy ORM data access (Req 19.7).

All database access goes through repositories. Repositories use the SQLAlchemy
ORM / Core expression language exclusively, which binds every value as a query
parameter -- there is no raw SQL string interpolation anywhere in this package
(Req 19.7, threat T5). Sensitive content is masked/sanitized by the relevant
repository BEFORE it reaches the database (Req 21, 19.6).
"""
