import src.Filter as Filters
from enum import Enum
from typing import Set, Callable

class FilterGroup:
    class Logic(Enum):
        AND = 1
        OR = 2

    def __init__(self, data, logic: 'FilterGroup.Logic' = 'FilterGroup.Logic.AND'):
        self.logic = logic
        self.filters: list[Filters.BaseFilter] = []
        self.subgroups: list[FilterGroup] = []
        self.data = data
        self.indices: Set[int] = set()

    def add_filter(self, type: Filters.Filter.Type, *args):
        self.filters.append(Filters.Filter(type, self.data, *args))
        return self

    def add_group(self, logic: 'FilterGroup.Logic' = 'FilterGroup.Logic.AND'):
        self.subgroups.append(FilterGroup(self.data, logic))
        return self

    def set_logic(self, logic: 'FilterGroup.Logic'):
        self.logic = logic

    def compute_filters(self):
        if not self.filters and not self.subgroups:
            return set(range(len(self.data)))

        results = []

        for filter_obj in self.filters:
            results.append(filter_obj.matching_indices)

        for subgroup in self.subgroups:
            results.append(subgroup.compute_filters())
        
        if not results:
            return set(range(len(self.data)))
        
        if self.logic == FilterGroup.Logic.AND:
            res = results[0].copy()
            for indices in results[1:]:
                res &= indices
            return res
        else:
            res = set()
            for indices in results:
                res |= indices
            return res

class FilterEngine:
    def __init__(self, data: list[dict]):
        self.data = data
        self.root = FilterGroup(data, FilterGroup.Logic.AND)
    
    def get_matching_indices(self) -> set[int]:
        return self.root.compute_filters()

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
    
    def filters(self):
        return self.root
    
    def __repr__(self):
        return f"<FilterEngine matching {len(self.get_matching_indices())} elements>"
    