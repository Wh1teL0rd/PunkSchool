"""
Strategy pattern for course sorting.
"""
from abc import ABC, abstractmethod
from sqlalchemy.orm import Query
from sqlalchemy import desc, func

from app.models.course import Course, Enrollment


class ICourseSortStrategy(ABC):
    """
    Interface for course sorting strategies.
    Implements the Strategy pattern.
    """
    
    @abstractmethod
    def sort(self, query: Query) -> Query:
        """
        Apply sorting to the query.
        
        Args:
            query: SQLAlchemy query object
        
        Returns:
            Sorted query
        """
        pass


class SortByPrice(ICourseSortStrategy):
    """Sort courses by price (ascending)."""
    
    def __init__(self, descending: bool = False):
        self.descending = descending
    
    def sort(self, query: Query) -> Query:
        if self.descending:
            return query.order_by(desc(Course.price))
        return query.order_by(Course.price)


class SortByRating(ICourseSortStrategy):
    """Sort courses by rating (descending by default)."""
    
    def __init__(self, descending: bool = True):
        self.descending = descending
    
    def sort(self, query: Query) -> Query:
        if self.descending:
            return query.order_by(desc(Course.rating))
        return query.order_by(Course.rating)


class SortByPopularity(ICourseSortStrategy):
    """Sort courses by number of enrollments (most popular first)."""
    
    def sort(self, query: Query) -> Query:
        # Sort by enrollment count descending
        return query.outerjoin(Enrollment).group_by(Course.id).order_by(
            desc(func.count(Enrollment.id))
        )


class SortByNewest(ICourseSortStrategy):
    """Sort courses by creation date (newest first)."""
    
    def sort(self, query: Query) -> Query:
        return query.order_by(desc(Course.created_at))


class SortByTitle(ICourseSortStrategy):
    """Sort courses alphabetically by title."""
    
    def __init__(self, descending: bool = False):
        self.descending = descending
    
    def sort(self, query: Query) -> Query:
        if self.descending:
            return query.order_by(desc(Course.title))
        return query.order_by(Course.title)


def get_sort_strategy(sort_by: str) -> ICourseSortStrategy:
    """
    Get the appropriate sorting strategy based on string parameter.
    
    Args:
        sort_by: Sorting method string
    
    Returns:
        Appropriate ICourseSortStrategy instance
    """
    strategies = {
        "price_asc": SortByPrice(descending=False),
        "price_desc": SortByPrice(descending=True),
        "rating": SortByRating(),
        "popularity": SortByPopularity(),
        "newest": SortByNewest(),
        "title": SortByTitle(),
    }
    
    return strategies.get(sort_by, SortByNewest())
