from sqlalchemy.orm import class_mapper

def to_dict(obj):
    """Convert SQLAlchemy model instance to dictionary."""
    if not obj:
        return None
    return {column.key: getattr(obj, column.key) for column in class_mapper(obj.__class__).columns}
