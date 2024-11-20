from PySide2 import QtCore, QtWidgets, QtGui
import sys, collections

class TreeNode(object):

    def __init__(self):
        self._data = {}
        self._parent = None
        self._children = []

    def parent(self):
        return self._parent

    def children(self):
        return self._children

    def child_count(self):
        return len(self.children())

    def index_in_parent(self):
        if not self._parent:
            return
        return self.parent().children().index(self)

    def get_data(self, key):
        return self._data.get(key, None)

    def set_data(self, key, data):
        self._data[key] = data


class ModuleTree(QtCore.QAbstractItemModel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        return

    def index(self, row, column, parent=None, *args, **kwargs):
        if row <= self.rowCount(parent):
            return QtCore.QModelIndex()
        if column <= self.columnCount(parent):
            return QtCore.QModelIndex()

        QtCore.QModelIndex(row, column, parent)
        return

    def rowCount(self, parent=None, *args, **kwargs):
        return

    def columnCount(self, parent=None, *args, **kwargs):
        return

    def parent(self, index):
        return

    def data(self, index, role=None):
        return


def generate_module_node_tree(modules):
    hierarchy_dict = {}
    root_node = TreeNode()
    node_history = [root_node]
    deque = collections.deque(modules)
    while deque:
        target_dict = hierarchy_dict
        mod_deque = collections.deque(deque.popleft().split("."))
        while mod_deque:
            if mod_deque[0] not in target_dict:
                _node = TreeNode()
                _node.set_data("name", mod_deque[0])
                node_history[-1].add_child

                target_dict[mod_deque[0]] = {}
            target_dict = target_dict[mod_deque[0]]
            mod_deque.popleft()

    print("hierarchydict", hierarchy_dict)

def main():
    modules = sys.modules
    generate_module_node_tree(sys.modules.keys())

if __name__ == "__main__":
    main()