from PySide2 import QtCore, QtWidgets, QtGui
import sys, collections
from maya import OpenMayaUI as omui
import difflib

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
        if node.parent() is None:
            node._parent = self

    def index_in_parent(self):
        if self._parent is None:
            return 0
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
        if not parent or not parent.isValid():
            return self.createIndex(row, column, self.root_node().children()[row])
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()
        _parent_node = parent.internalPointer()

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
        if _node.parent() is None:
            return QtCore.QModelIndex()
        _parent_node = _node.parent()
        if _parent_node.parent() is None:
            return QtCore.QModelIndex()
        _parents_parent = self.createIndex(_parent_node.parent().index_in_parent(), 0, _parent_node.parent())
        return self.index(row=_parent_node.index_in_parent(), column=0, parent=_parents_parent)

    def data(self, index, role=None):
        if not index.isValid():
            return None
        if role != QtCore.Qt.DisplayRole:
            return None
        _node = index.internalPointer()
        return _node.get_data("name")

class ProxyModel(QtCore.QSortFilterProxyModel):

    def __init__(self):
        super().__init__()
        self._filter_text = ""
        self._ratio_threshhold = 0.4

        self._ratio_cache = {}

    def set_filter_text(self, text):
        self._ratio_cache = {}
        # print('filterupdate', text)
        self._filter_text = text
        self.invalidate()

    def filter_text(self):
        return self._filter_text

    def filterAcceptsColumn(self, source_column, source_parent):
        return True

    def filterAcceptsRow(self, source_row, source_parent):

        name = (self.sourceModel().data(self.sourceModel().index(source_row, 0, source_parent), QtCore.Qt.DisplayRole)).lower()
        if not name:
            return False
        if self.filter_text() in name:
            return True

        _ratio = difflib.SequenceMatcher(None, self.filter_text(), name).real_quick_ratio()

        self._ratio_cache[name] = _ratio
        # print(_ratio)
        if _ratio > self._ratio_threshhold:
            # print("DELETE", name)
            return False
        return True

    def lessThan(self, source_left, source_right):
        # print("lessthan")
        if not self.filter_text():
            return source_left.row() < source_right.row()
        _left_ratio = self._ratio_cache.get(source_left, difflib.SequenceMatcher(None, self.filter_text(), (source_left.data()).lower()).quick_ratio())
        _right_ratio = self._ratio_cache.get(source_right, difflib.SequenceMatcher(None, self.filter_text(), (source_right.data()).lower()).quick_ratio())

        return _left_ratio < _right_ratio

    # def data(self, index, role=QtCore.Qt.DisplayRole):
    #     if role != QtCore.Qt.DisplayRole:
    #         return
    #     # Provides a color falloff to demonstrate the filtering
    #     if not self.filter_text() or self._ratio_threshhold <= 0.0:
    #         return super().data(index, role)
    #     # ratio = difflib.SequenceMatcher(None, self.filter_text(), (self.sourceModel().data(index, role) or "").lower()).quick_ratio()
    #     _data = super().data(index, role)
    #     if not _data:
    #         super().moveRow(index.parent(), index.row(), QtCore.QModelIndex(), -1)
    #         # self.removeRow(index.row(), index.parent())
    #         return
    #     ratio = difflib.SequenceMatcher(None, self.filter_text(), _data.lower()).quick_ratio()
    #     if ratio < self._ratio_threshhold:
    #         # self.removeRow(index.row(), index.parent())
    #         super().moveRow(index.parent(), index.row(), QtCore.QModelIndex(), -1)
    #         # Draw falloff color between 20 (no match) and 255 (full match)
    #         t = ratio * (1.0/self._ratio_threshhold)
    #         luminance = (1 - t) * 20 + t * 255
    #
    #         return QtGui.QBrush(QtGui.QColor(luminance, luminance, luminance))
    #     return super().data(index, role)


class ModuleToolbar(QtWidgets.QToolBar):
    reload_pressed = QtCore.Signal()
    filter_edited = QtCore.Signal(str)


    def __init__(self):
        super().__init__()

        reload_button = QtWidgets.QToolButton()
        reload_button.setText("Reload")
        reload_button.clicked.connect(self.reload_pressed.emit)


        self.search_line = QtWidgets.QLineEdit()
        self.search_line.setPlaceholderText("Search...")
        self.search_line.textChanged.connect(self.emit_filter_edited)

        self.addWidget(reload_button)
        self.addWidget(self.search_line)

    def emit_filter_edited(self):
        self.filter_edited.emit(self.search_line.text())


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

    def update_filter(self, text):
        self.view.model().set_filter_text(text)
        return




def generate_module_node_tree(modules):
    hierarchy_dict = {}
    root_node = TreeNode()
    root_node.set_data("name", "ROOT")
    node_history = [root_node]
    deque = collections.deque(modules)
    while deque:
        target_dict = hierarchy_dict
        mod_deque = collections.deque(deque.popleft().split("."))
        while mod_deque:
            _mod = mod_deque.popleft()
            if _mod not in target_dict:
                _node = TreeNode()
                _node.set_data("name", _mod)
                _parent_node = target_dict.get("NODE", root_node)
                _parent_node.add_child(_node)
                target_dict[_mod] = {"NODE": _node}
            target_dict = target_dict[_mod]
    return root_node

def print_node_tree(root_node, depth=0):
    deque = collections.deque()
    deque.append(root_node)
    branch_out = ("——"*depth + "|")
    branch_down = "|"
    prefix = branch_down + branch_out

    module = sys.modules.get(root_node.get_data("name"))
    path = ""
    if module and hasattr(module, "__file__"):
        path = module.__file__

    print(prefix + root_node.get_data("name") + "||" + path)

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
    toolbar.filter_edited.connect(controller.update_filter)
    sorting_proxy_model = ProxyModel()
    sorting_proxy_model.setSourceModel(ModuleTree(root))
    sorting_proxy_model.setRecursiveFilteringEnabled(True)
    sorting_proxy_model.setDynamicSortFilter(True)
    view.setModel(sorting_proxy_model)
    view.setSortingEnabled(True)
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