from typing import List, Any, Tuple

import tkinter
import tkinter.ttk as ttk
import customtkinter


__all__ = ["TreeViewWidget"]


class TreeViewWidget(customtkinter.CTkFrame):
    def __init__(self, data: List[List], column_titles: List[str], text_width=400, number_width=50, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.data = list(data)
        self.column_titles = column_titles
        self.data_types = [type(val) for val in data[0]]

        tree_frame = customtkinter.CTkFrame(self)
        # Create Tree for display
        tree = ttk.Treeview(tree_frame, columns=self.column_titles, show='headings')
        tree.grid(row=0, column=0, sticky="nsew")
        tree.columnconfigure(0, weight=1)
        for col_idx, (column, data_type) in enumerate(zip(self.column_titles, self.data_types)):
            tree.heading(column, text=column, command=lambda col_idx=col_idx: self.sort_rows(int(col_idx)))
            col_width = text_width if data_type is str else number_width
            tree.column(col_idx, width=col_width)
        # Create scrollbar
        vertical_scroll = customtkinter.CTkScrollbar(tree_frame, orientation="vertical", command=tree.yview)
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=vertical_scroll.set)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)

        self.tree = tree
        self.tree_add(list(data))
        self.col_sort_reverse = [False] * len(self.column_titles)

    def child_values(self, child):
        return self.tree.item(child)["values"]

    def tree_remove(self, children=None) -> None:
        """
        Removes all children if children is None. Else, just delete the specified children
        :param children:
        """
        children_to_delete = self.tree.get_children() if children is None else children
        for child in children_to_delete:
            self.tree.delete(child)

    def tree_add(self, items: List[List[Any]], position=tkinter.END) -> None:
        """
        Add new rows to the tree view
        :param items: List of rows to add to list
        :param position: Position to add it to. By default, row added to the end of the list.
        """
        for item in items:
            self.tree.insert("", position, values=item)

    def get_children(self, *args, **kwargs) -> Tuple[str, ...]:
        """ Returns all items in the rows """
        return self.tree.get_children(*args, **kwargs)

    def selection(self) -> Tuple[str, ...]:
        """ Returns currently selected rows """
        return self.tree.selection()

    def reset(self) -> None:
        """ Resets view back to default """
        self.tree_remove()
        self.tree_add(self.data)
        self.col_sort_reverse = [False] * len(self.column_titles)

    def sort_rows(self, col_idx) -> None:
        """
        Sort by column idx.
        :param col_idx:  Index which we want to sort
        """
        self.col_sort_reverse[col_idx] = not self.col_sort_reverse[col_idx]
        rows = [self.child_values(child) for child in self.get_children()]
        data_type = self.data_types[col_idx]
        rows.sort(key=lambda row: data_type(row[col_idx]), reverse=self.col_sort_reverse[col_idx])
        self.tree_remove()
        self.tree_add(rows)

    def remove_selected(self):
        """ Removes currently selected rows """
        self.tree_remove(self.selection())
