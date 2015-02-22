"""This module provides the means for tagging servers.

Server tags are simple strings that are used to referencing the server's
configuration. For example, a tag is used to identify the game the server
is played (e.g. 'tf2' or 'csgo') and the gamemode of the map.
"""


import venusian


class TaggerError(Exception):
    pass


class DependancyError(TaggerError):
    pass


class CyclicDependancyError(DependancyError):
    pass


class TaggerImplementation:

    def __init__(self, tag, implementation, dependancies):
        self.tag = tag
        self._implementation = implementation
        self._named_dependancies = frozenset(dependancies)
        self._dependancies = None

    @property
    def dependancies(self):
        if self._dependancies is None:
            raise AttributeError("Dependancies haven't been resolved yet.")
        return self._dependancies

    def find_dependancies(self, taggers):
        tags = {tagger.tag: tagger for tagger in taggers}
        dependancies = []
        for dep in self._named_dependancies:
            if dep not in tags:
                raise DependancyError(
                    "Cannot resolve dependancy on {dep!r} for {tag!r} as "
                    "{dep!r} does not exist".format(dep=dep_tag,
                                                    tag=tagger.tag))
            dependancies.append(tags[dep])
        self._dependancies = tuple(dependancies)

    def __repr__(self):
        return ("<Tag {tag!r} implmented by "
                "{_implementation}>".format(**vars(self)))

    def __call__(self, info, players, rules, tags):
        return self._implementation(info, players, rules, tags)


class Tagger:
    """Tag evaluator.

    Instances of this class are used to determine the tags that apply to
    a server configuration. It will resolve the tag dependancies so that
    tag functions are called in the correct order.

    This class should never be instantiated directly. Use :meth:`scan`
    instead.
    """

    def __init__(self, *taggers):
        """Initialise the tag evaluator.

        This takes any number of taggers and resolves their dependancies.
        If there are two implementations for the same tag name then
        :exc:`TaggerError` is raised.

        :param taggers: zero or more :class:`TaggerImplementation` objects.
        """
        tags = {}
        for tagger in taggers:
            if tagger.tag in tags:
                raise TaggerError(
                    "Duplicate implementations of the {tag!r} tag; {0!r} "
                    "{1!r}".format(
                        tags[tagger.tag],
                        tagger,
                        tag=tagger.tag))
            tags[tagger.tag] = tagger
        self.taggers = self._resolve_dependancies(tags.values())

    @staticmethod
    def _resolve_dependancies(taggers):
        """Order tag implementations based on their dependancies.

        Given an iterable of taggers this will return them sorted into a list
        so that the depended upon taggers come before those which are
        dependant on them.

        :raises CyclicDependancyError: should there be any cyclic dependacies
            within the given taggers.
        :returns: a topologically sorted list of taggers.
        """
        for tagger in taggers:
            tagger.find_dependancies(taggers)
        ordered = []
        marked = set()
        temp_marked = set()

        def visit(tagger):
            if tagger.tag in temp_marked:
                raise CyclicDependancyError(
                    "{tag!r} has cyclical dependancies".format(tag=tagger.tag))
            if tagger.tag not in marked:
                temp_marked.add(tagger.tag)
                for dep in tagger.dependancies:
                    visit(dep)
                marked.add(tagger.tag)
                temp_marked.remove(tagger.tag)
                ordered.append(tagger)

        for tagger in taggers:
            if tagger.tag not in marked:
                visit(tagger)
        return ordered

    @classmethod
    def scan(cls, package):
        scanner = venusian.Scanner(taggers=[])
        scanner.scan(package, categories=["serverstf.taggers"])
        return cls(*scanner.taggers)

    def evaluate(self, info, players, rules):
        tags = set()
        for tagger in self.taggers:
            if tagger(info, players, rules, frozenset(tags)):
                tags.add(tagger.tag)
        return tags


def tag(tag, dependancies=()):
    """A decorator for defining tags.

    Functions marked with this decorator will be picked up by
    :meth:`Tagger.scan` and included for tag evaluation.

    The wrapped function should take four arguments: the server info, player
    list, cvars/rules list and a set of currently applied tags. If the return
    value is truthy then the named `tag` is applied otherwise it is not.

    Tags may have a dependancy on other tags. This will mean that the
    :class:`Tagger` instance running them will only invoke the wrapped function
    after all of its dependancies have been tested. Its these dependancies
    which are used to populate the fourth argument.

    .. note::

        Marking as tag as a dependancy doesn't mean it's guaranteed to be
        present in set of tags passed as the fourth argument. Checking its
        existing within the set is the responsiblity of the wrapped function.

    Care must be taken to avoid creating circular dependancies between tags.

    :param str tag: The name of the tag.
    :param dependancies: A sequence off tag names that must be evaluated
        before this *this* one.
    """

    def callback(scanner, name, obj):
        scanner.taggers.append(TaggerImplementation(tag, obj, dependancies))

    def decorator(function):
        venusian.attach(function, callback, category="serverstf.taggers")
        return function

    return decorator


@tag("mge", ["tf2"])
def mge(info, players, rules, tags):
    return "tf2" in tags and info["map"].startswith("mge_")


@tag("tf2")
def tf2(info, players, rules, tags):
    return info["app_id"] == 440


if __name__ == "__main__":
    import sys

    tagger = Tagger.scan(sys.modules[__package__])
    print(tagger.evaluate({"app_id": 440, "map": "ctf_2fort"}, None, None))
