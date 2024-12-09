from PySide2 import QtCore, QtWidgets, QtGui
import sys, collections
from maya import OpenMayaUI as omui

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

    def add_child(self, node, index=-1):
        self.children().insert(index, node)

    def index_in_parent(self):
        if not self._parent:
            return
        return self.parent().children().index(self)

    def get_data(self, key):
        return self._data.get(key, None)

    def set_data(self, key, data):
        self._data[key] = data


class ModuleTree(QtCore.QAbstractItemModel):

    def __init__(self, root_node, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._root_node = root_node
        return

    def root_node(self):
        return self._root_node

    def index(self, row, column, parent=None, *args, **kwargs):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()
        if not parent.isValid():
            return self.createIndex(row, column, self.root_node().children()[row])

        _parent_node = parent.internalPointer()
        if not isinstance(_parent_node, TreeNode):
            return QtCore.QModelIndex()

        _node = _parent_node.children()[row]
        index = self.createIndex(row, column, _node)

        return index

    def rowCount(self, parent=None, *args, **kwargs):
        if not parent.isValid():
            return self.root_node().child_count()
        return parent.internalPointer().child_count()

    def columnCount(self, parent=None, *args, **kwargs):
        return 1

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        _node = index.internalPointer()
        if not _node.parent():
            return QtCore.QModelIndex()
        _parent_node = _node.parent()
        return self.index(_parent_node.index_in_parent(), 0, _parent_node.parent())

    def data(self, index, role=None):
        if not index.isValid():
            return None
        if role != QtCore.Qt.DisplayRole:
            return None
        _node = index.internalPointer()
        return _node.get_data("name")



class ModuleToolbar(QtWidgets.QToolBar):
    reload_pressed = QtCore.Signal()


    def __init__(self):
        super().__init__()

        reload_button = QtWidgets.QToolButton()
        reload_button.setText("Reload")
        reload_button.clicked.connect(self.reload_pressed.emit)

        self.addWidget(reload_button)


class HotReloaderFederalController(QtCore.QObject):

    def __init__(self, view):
        """

        Parameters
        ----------
        view: QtWidgets.QTreeView
        """
        super().__init__()
        self.view = view

    def reload_selection(self):
        """
        Deletes selected module names from sys modules
        Returns
        -------

        """
        print("RELOAD")
        selection_model = self.view.selectionModel()
        indexes = selection_model.selectedIndexes()
        nodes = [index.internalPointer() for index in indexes]
        module_names = [node.get_data("name") for node in nodes]
        for module in sys.modules.copy():
            for _mod in module_names:
                if module.startswith(_mod):
                    print("deleting", _mod)
                    del sys.modules[module]




def generate_module_node_tree(modules):
    hierarchy_dict = {}
    root_node = TreeNode()
    root_node.set_data("name", "ROOT")
    node_history = [root_node]
    deque = collections.deque(modules)
    while deque:
        target_dict = hierarchy_dict
        mod_deque = collections.deque(deque.popleft().split("."))
        print(mod_deque)
        while mod_deque:
            if mod_deque[0] not in target_dict:
                _node = TreeNode()
                _node.set_data("name", mod_deque[0])
                _parent_node = target_dict.get("NODE", root_node)
                _parent_node.add_child(_node)
                target_dict[mod_deque[0]] = {"NODE": _node}
            target_dict = target_dict[mod_deque[0]]
            mod_deque.popleft()
    return root_node

def print_node_tree(root_node, depth=0):
    deque = collections.deque()
    deque.append(root_node)
    branch_out = ("——"*depth + "|")
    branch_down = "|"
    prefix = branch_down + branch_out

    print(prefix + root_node.get_data("name"))

    depth += 1
    for _node in root_node.children():
        print_node_tree(_node, depth)
    # while deque:
    #     _node = deque.popleft()
    #     print(prefix + _node.get_data("name"))
    #     prefix += branch_down
    #     if _node.children():
    #         prefix += branch_out
    #     deque.extend(_node.children())


    # print("hierarchydict", hierarchy_dict)




def hot_reloader_window(parent=None):
    root = generate_module_node_tree(sys.modules.keys())
    print_node_tree(root)
    win = QtWidgets.QMainWindow(parent=parent)
    toolbar = ModuleToolbar()


    win.addToolBar(QtCore.Qt.TopToolBarArea,toolbar)
    view = QtWidgets.QTreeView()
    controller = HotReloaderFederalController(view = view)
    win._controller = controller
    toolbar.reload_pressed.connect(controller.reload_selection)
    view.setModel(ModuleTree(root))
    win.setCentralWidget(view)
    return win




def _maya_main():
    from shiboken2 import wrapInstance
    main_window = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QMainWindow)
    win = hot_reloader_window(main_window)
    win.show()


def main(standalone=False):

    if standalone:
        _app = QtWidgets.QApplication()
        win = hot_reloader_window()
        win.show()
        sys.exit(_app.exec_())
        return

    _maya_main()

if __name__ == "__main__":
    main(True)