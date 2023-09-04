from typing import List


__all__ = ["SearchTrie"]


class TrieNode:
    def __init__(self):
        self.children = {}
        self.indices = []


class SearchTrie:
    def __init__(self, strings: List[str]):
        self.trie = TrieNode()
        self.strings = []

        for string in strings:
            self.add(string)

    def reset(self):
        self.trie = TrieNode()

    def add(self, string):
        str_idx = len(self.strings)
        self.strings.append(string)

        current_node = self.trie
        for character in string:
            node = current_node.children.get(character, TrieNode())
            node.indices.append(str_idx)
            current_node.children[character] = node
            current_node = node

    def search(self, prefix):
        current_node = self.trie
        for character in prefix:
            node = current_node.children.get(character, TrieNode())
            if node is None:
                return node
            current_node = node
        return current_node

    def tab_completion(self, prefix):
        """
        Get common string for children nodes starting with prefix

        e.g. abc_123_def, abc_123_ijk, abc_123_lmn
        prefix = 'abc', returns '_123_'

        :param prefix: Prefix to look for
        :return: Common string for child nodes with prefix
        """
        current_node = self.search(prefix)

        output_string = ""
        while len(current_node.children) == 1:
            character, node = list(current_node.children.items())[0]
            output_string += character
            current_node = node
        return output_string
