from __future__ import unicode_literals, print_function


class Helper(object):
    pass


class SearchSetsByTitle(Helper):
    def search(self, title, elements):
        results = []
        for element in elements:
            if title.lower() in element.Title.lower():
                results.append(element)
            if 'Elements' in element:
                results += self.search(title, element.Elements)
        return results

    def __call__(self, api, title, username=None):
        hierarchy = api.LoadGroupHierarchy(username)
        return self.search(title, hierarchy.Elements)


search_sets_by_title = SearchSetsByTitle()
