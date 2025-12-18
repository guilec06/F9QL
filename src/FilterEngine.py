from src.Filter import FilterType, BaseFilter, Filter, AlwaysTrueFilter
from enum import Enum
from typing import Set, Callable

class FilterGroup:
    class Logic(Enum):
        AND = 1
        OR = 2
        NOT = 3

    def __init__(self, logic: 'FilterGroup.Logic | None' = None):
        self.logic = logic or FilterGroup.Logic.AND
        self.filters: list[BaseFilter] = []
        self.subgroups: list[FilterGroup] = []
        self.indices: Set[int] = set()

    def add_filter(self, type: FilterType, *args):
        self.filters.append(Filter(type, *args))
        return self

    def add_group(self, group: 'FilterGroup'):
        self.subgroups.append(group)
        return self

    def set_logic(self, logic: 'FilterGroup.Logic'):
        self.logic = logic

    def compute_matches(self, data):
        if not self.filters and not self.subgroups:
            return set(range(len(data)))

        results = []

        for filter_obj in self.filters:
            filter_obj.compute_matches(data)
            results.append(filter_obj.matching_indices)

        for subgroup in self.subgroups:
            results.append(subgroup.compute_matches(data))
        
        if not results:
            return set(range(len(data)))
        
        if self.logic == FilterGroup.Logic.AND:
            res = results[0].copy()
            for indices in results[1:]:
                res &= indices
            return res
        elif self.logic == FilterGroup.Logic.OR:
            res = set()
            for indices in results:
                res |= indices
            return res
        else:
            res = set(range(len(data)))
            for indices in results:
                res -= indices
            return res
            

    def __and__(self, other: 'FilterGroup | BaseFilter'):
        combined = FilterGroup(FilterGroup.Logic.AND)
        combined.subgroups.append(self)
        if isinstance(other, FilterGroup):
            combined.subgroups.append(other)
        else:
            combined.filters.append(other)
        return combined

    def __or__(self, other: 'FilterGroup | BaseFilter'):
        combined = FilterGroup(FilterGroup.Logic.OR)
        combined.subgroups.append(self)
        if isinstance(other, FilterGroup):
            combined.subgroups.append(other)
        else:
            combined.filters.append(other)
        return combined
    
    def __invert__(self):
        negated = FilterGroup(FilterGroup.Logic.NOT)
        negated.subgroups.append(self)
        return negated


class FilterEngine:
    def __init__(self, data: list[dict]):
        self.data = data
        self.filters = AlwaysTrueFilter()
    
    def get_matching_indices(self) -> set[int]:
        return self.filters.compute_matches(self.data)

    def get_messages(self, limit: int | None = None, sort_key: Callable | str | None = None, reverse: bool = False):
        matching_indices = self.get_matching_indices()
        sorted_indices = sorted(matching_indices)

        if sort_key:
            # If sort_key is a string, convert it to an attribute getter function
            if isinstance(sort_key, str):
                attr_name = sort_key
                sort_key = lambda msg: getattr(msg, attr_name)
            
            sorted_indices = sorted(sorted_indices, key=lambda i: sort_key(self.data[i]), reverse=reverse)
        
        if limit:
            sorted_indices = sorted_indices[:limit]
        
        return [self.data[i] for i in sorted_indices]
    
    def __repr__(self):
        return f"<FilterEngine matching {len(self.get_matching_indices())} elements>"
    