import sqlalchemy

metadata = sqlalchemy.MetaData()

filters = sqlalchemy.Table(
    "filters",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String(50), primary_key=True),
    sqlalchemy.Column("driving_mode", sqlalchemy.SmallInteger, nullable=True),
    sqlalchemy.Column("datetime", sqlalchemy.SmallInteger, nullable=True),
    sqlalchemy.Column("triggered_cause", sqlalchemy.SmallInteger, nullable=True),
    sqlalchemy.Column("zones", sqlalchemy.SmallInteger, nullable=True),
    sqlalchemy.Column("road_types", sqlalchemy.SmallInteger, nullable=True),
    sqlalchemy.Column("intersections", sqlalchemy.SmallInteger, nullable=True),
    sqlalchemy.Column("roundabouts", sqlalchemy.SmallInteger, nullable=True),
    sqlalchemy.Column("cloudness", sqlalchemy.SmallInteger, nullable=True),
    sqlalchemy.Column("wind", sqlalchemy.SmallInteger, nullable=True),
    sqlalchemy.Column("rainfall", sqlalchemy.SmallInteger, nullable=True),
    sqlalchemy.Column("snowfall", sqlalchemy.SmallInteger, nullable=True),
    sqlalchemy.Column("illuminance", sqlalchemy.SmallInteger, nullable=True),
    sqlalchemy.Column("created_at", sqlalchemy.TIMESTAMP, server_default=sqlalchemy.text('CURRENT_TIMESTAMP')),
)

filter_special_structures = sqlalchemy.Table(
    "filter_special_structures",
    metadata,
    sqlalchemy.Column("filter_id", sqlalchemy.String(50), sqlalchemy.ForeignKey("filters.id"), primary_key=True),
    sqlalchemy.Column("structure_code", sqlalchemy.SmallInteger, primary_key=True),
)
