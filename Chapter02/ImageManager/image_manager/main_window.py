"""Image Manager GUI, Part 2
Adds features for managing files, user settings, and dialogs 

Building Custom UIs with PyQt with Packt Publishing
Chapter 2 - Building the Foundation for GUIs
Created by: Joshua Willman
"""

# Import necessary modules
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, 
    QDockWidget, QListWidgetItem, QFileDialog, QMessageBox, QScrollArea)
from PyQt6.QtCore import (Qt, QByteArray, QSize, QPoint, QDir, QFile, 
    QFileInfo, QSysInfo, QSettings)
from PyQt6.QtGui import QIcon, QAction, QKeySequence
# Import relative modules
from .widgets.image_viewer import ImageViewerListWidget
from .dialogs.image_info_dialog import ImageInfoDialog
from .dialogs.preferences import PreferencesDialog

class MainWindow(QMainWindow):

    # Create a QSettings object rather than storing values. Pass in a company 
    # name and an application name
    settings = QSettings("Custom GUIs", "Image Manager GUI")
    #print(settings.fileName()) # NOTE: Uncomment to print the path to settings

    images_path = "Images" # File path to the Images directory
    image_dir = QDir(images_path)
    info_dialog = None # Create variable for modeless dialog

    def __init__(self):
        """MainWindow Constructor for Image Manager"""
        super().__init__() # Constructor for QMainWindow
        self.initializeUI()

    def initializeUI(self):
        """Set up the GUI's main window and load initial settings and data."""
        self.setWindowTitle("Image Manager")
        self.setObjectName("ImageManager")

        # Set up the main window, menu, dock widgets, and initialize the GUI's settings
        self.setUpMainWindow()
        self.displayImagePreviewDock()
        self.createActions()
        self.createMenus()
        self.loadStoredImageData()
        self.getInitialSettings()
        self.show() # Display the main window

    def setUpMainWindow(self):
        """Set up the application's main window containing the QListWidget."""
        self.image_view_lw = ImageViewerListWidget(self)
        # Use signals/slots to interact with the list widget 
        self.image_view_lw.itemSelectionChanged.connect(self.updateDockInfo)
        self.image_view_lw.itemDoubleClicked.connect(self.displayImageInfoDialog)
        # Use the list widget's internal model to enable/disable menu items
        self.image_view_lw.model().rowsInserted.connect(self.manageMenuItems)
        self.image_view_lw.model().rowsRemoved.connect(self.manageMenuItems)

        self.setCentralWidget(self.image_view_lw)

    def createActions(self):
        """Create the application's menu actions."""
        # Create actions for File menu
        self.import_act = QAction("Import Images...", self, triggered=self.importImages)
        self.import_act.setShortcut("Ctrl+I") 

        self.preferences_act = QAction("Preferences...", self, triggered=self.showPreferencesDialog)

        self.quit_act = QAction("Quit Task Manager", self, triggered=self.close)
        self.quit_act.setShortcut(QKeySequence.StandardKey.Quit) # Ctrl+Q

        # Create actions for Edit menu
        self.select_all_act = QAction("Select All", self, triggered=self.image_view_lw.selectAll)
        self.select_all_act.setShortcut(QKeySequence.StandardKey.SelectAll) # Ctrl+A

        self.delete_act = QAction("Delete Images", self, triggered=self.deleteImages)
        self.delete_act.setShortcut(QKeySequence.StandardKey.Delete) # Del
        self.delete_act.setEnabled(False)

        # Create actions for View menu
        # Handle the visibility of the dock widget that displays images
        self.show_dock_act = self.image_preview_dock.toggleViewAction()
        self.show_dock_act.setText("Show Image View")  

        self.sort_ascend_act = QAction("Sort Ascending", self,
            triggered=lambda: self.sortListItems(Qt.SortOrder.AscendingOrder))
        self.sort_ascend_act.setEnabled(False)

        self.sort_descend_act = QAction("Sort Descending", self,
            triggered=lambda: self.sortListItems(Qt.SortOrder.DescendingOrder))
        self.sort_descend_act.setEnabled(False)

        self.fullscreen_act = QAction("Show Fullscreen", self, 
            triggered=self.displayFullScreen, checkable=True)

        # Create actions for Help menu
        self.about_act = QAction("About Image Manager", 
            self, triggered=self.showAboutDialog)  

    def createMenus(self):
        """Create the application's menu."""
        if QSysInfo.productType() == "macos" or "osx":
            self.menuBar().setNativeMenuBar(False)

        self.file_menu = self.menuBar().addMenu("&File")
        self.file_menu.addAction(self.import_act)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.preferences_act)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.quit_act)

        self.edit_menu = self.menuBar().addMenu("&Edit")
        self.edit_menu.addAction(self.select_all_act)
        self.edit_menu.addSeparator()
        self.edit_menu.addAction(self.delete_act)  

        self.view_menu = self.menuBar().addMenu("&View")
        self.view_menu.addAction(self.show_dock_act)  
        self.view_menu.addSeparator()
        self.view_menu.addAction(self.sort_ascend_act)
        self.view_menu.addAction(self.sort_descend_act)
        self.view_menu.addSeparator()
        self.view_menu.addAction(self.fullscreen_act)       

        self.help_menu = self.menuBar().addMenu("&Help")
        self.help_menu.addAction(self.about_act)        

    def manageMenuItems(self, parent, first, last):
        """Slot to enable/disable menu items if rows have been 
        added/deleted to QListWidget. The rowsInserted() and 
        rowsRemoved() that trigger this slot return the 'parent',
        'first', and 'last' values, but they are not used in 
        this method."""
        if self.image_view_lw.count() == 0:
            self.delete_act.setEnabled(False)
            self.sort_ascend_act.setEnabled(False)
            self.sort_descend_act.setEnabled(False)
        elif self.image_view_lw.count() > 0:
            self.delete_act.setEnabled(True)
            self.sort_ascend_act.setEnabled(True)
            self.sort_descend_act.setEnabled(True)   

    def displayImagePreviewDock(self):
        """Dock widget that displays a selected image in a scrollable 
        area and uses its file name as the dock's title."""
        self.image_preview_dock = QDockWidget()
        self.image_preview_dock.setObjectName("PreviewDock")
        self.image_preview_dock.setWindowTitle("Show Image View")
        self.image_preview_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)

        self.display_image_label = QLabel()
        self.display_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.view_scroll_area = QScrollArea()
        self.view_scroll_area.setMinimumWidth(300)
        self.view_scroll_area.setWidgetResizable(True)

        self.image_preview_dock.setWidget(self.view_scroll_area)
        # Set initial location of dock widget in the main window
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.image_preview_dock)   

    def updateDockInfo(self):
        """Slot to update the image that the dock widget displays."""
        # Only display an image if one item is selected
        if (len(self.image_view_lw.selectedItems()) == 0 or 
            len(self.image_view_lw.selectedItems()) > 1):
            self.image_preview_dock.setWindowTitle("Show Image View")
            self.display_image_label.clear()
        else:
            curr_item = self.image_view_lw.currentItem()
            self.image_preview_dock.setWindowTitle(curr_item.text())
            self.show_dock_act.setText("Show Image View") 

            # Get the current height of the dock widget
            dock_height = self.image_preview_dock.height()
            # Get the size of the original image/item
            icon_size = curr_item.icon().availableSizes()[0]
            icon_width = icon_size.width()

            # Return a pixmap from the item's icon and display in the scroll area
            pixmap = curr_item.icon().pixmap(QSize(icon_width, dock_height)) 
            self.display_image_label.setPixmap(pixmap)
            self.view_scroll_area.setWidget(self.display_image_label) 
        
    def importImages(self):
        """Import the images a user selects, remove duplicates, and add
        items to the QListWidget."""
        duplicate_images = [] # Store the names of duplicate images
        image_paths, _ = QFileDialog.getOpenFileNames(self, 
            "Select Image Files", "", "Images (*.png *.xpm *.jpg *.jpeg)")

        if image_paths:
            if self.image_dir.exists():
                for image_path in image_paths:
                    # Pass image path to QFileInfo object
                    image_info = QFileInfo(image_path) 
                    file_name = image_info.fileName()
                    item_name = image_info.baseName()

                    # Copy the files into the Images directory, check for files 
                    # with the same name
                    new_name = self.image_dir.absolutePath() + f"/{file_name}"
                    file_exists = QFile.copy(image_path, new_name)
                    if file_exists == False:
                        duplicate_images.append(image_path)
                    else:
                        self.createListItems(image_path, item_name, image_info, new_name)
                        if self.is_delete_checked == True: # Handle deleting images
                            QFile.moveToTrash(image_path) 
            else:
                QMessageBox.warning(self, "Images Location Not Found",
                    """<p>The Images Location cannot be found. Restart the application to
                    recreate the directory.</p>""")

        # Display a custom dialog to inform the user of duplicate images
        if len(duplicate_images) != 0:
            duplicates_dialog = QMessageBox(self)
            duplicates_dialog.setIcon(QMessageBox.Icon.Information)
            duplicates_dialog.setWindowTitle("Duplicate Images")
            duplicates_dialog.setText("""<p>Some images were not imported because 
                they already exist.</p>""")

            details = '\n'.join([item for item in duplicate_images])
            duplicates_dialog.setDetailedText(details)
            duplicates_dialog.exec()

            duplicate_images.clear() # Clear the list 
        # Check if window is still in focus. If not, give it focus
        if self.isActiveWindow() == False:
            self.activateWindow()

    def createListItems(self, image_path, item_name, image_info, new_name=None):
        """Simple method for creating QListWidgetItem objects. 
        'image_path': the path to the file.
        'item_name': the base name used for QListWidgetItem objects.
        'image_info': the QFileInfo object.
        'new_name': used when importing new photos, making sure the program
        points to the new image location."""
        list_item = QListWidgetItem(QIcon(image_path), item_name)
        self.image_view_lw.setIconSize(QSize(80, 80))
        self.image_view_lw.addItem(list_item)
        if new_name != None:
            image_info.setFile(new_name)
        self.image_view_lw.images_info_list.append(image_info) 

    def sortListItems(self, order): 
        """First, sort the items in the QListWidget using sortItems(). Then handle 
        sorting the QFileInfo objects in the images_info_list using Python's sort() to 
        match how the QListWidget sorts items."""
        self.image_view_lw.sortItems(order)
        if order == Qt.SortOrder.AscendingOrder:
            self.image_view_lw.images_info_list.sort(key=lambda item: (item.baseName().upper(), item.baseName()[0].islower()))
        elif order == Qt.SortOrder.DescendingOrder:
            self.image_view_lw.images_info_list.sort(reverse=True, key=lambda item: (item.baseName().upper(), item.baseName()[0].islower()))

    def deleteImages(self):
        """Delete images from the QListWidget and from where images
        are stored on disk."""
        number_of_photos = len(self.image_view_lw.selectedItems())
        answer = QMessageBox.warning(self, "Delete Image(s)", 
            f"Are you sure you want to delete {number_of_photos} image(s)?", 
            QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes, 
            QMessageBox.StandardButton.No)

        if answer == QMessageBox.StandardButton.Yes:
            for item in self.image_view_lw.selectedItems():
                index = self.image_view_lw.indexFromItem(item).row()
                # Get the image's information before deletion
                image_info = self.image_view_lw.images_info_list[index] 

                # Remove items from the Images directory, from the list widget, 
                # and the images_info_list that stores QFileInfo objects
                QFile.moveToTrash(image_info.absoluteFilePath()) 
                self.image_view_lw.takeItem(index)
                del self.image_view_lw.images_info_list[index] 
                del item        

    def loadStoredImageData(self):
        """Load images from the Images directory. The Images directory is 
        created the first time running the application."""
        if not(self.image_dir.exists()):
            QDir().mkdir(self.images_path)
        elif self.image_dir.exists():
            # Create a list of the files in the Images directory
            images = self.image_dir.entryInfoList(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)
            for image in images: 
                # Imported files are QFileInfo objects
                item_name = image.baseName()
                path = image.absoluteFilePath()
                self.createListItems(path, item_name, image) 

    def displayImageInfoDialog(self, item): 
        """Display image metadata in a modeless dialog box. 'index' is the index of 
        the item that is clicked on."""
        index = self.image_view_lw.indexFromItem(item).row()
        if self.info_dialog == None: 
            self.info_dialog = ImageInfoDialog(self, self.image_view_lw.images_info_list[index])
        elif self.info_dialog != None:
            self.info_dialog.close()
            self.info_dialog = ImageInfoDialog(self, self.image_view_lw.images_info_list[index])
        self.info_dialog.show()         

    def showPreferencesDialog(self):
        """Display the application's preferences dialog. Save the value of the 
        delete_images_checkbox in the settings."""
        prefs_dialog = PreferencesDialog(self, self.image_dir, self.is_delete_checked)
        response = prefs_dialog.exec()

        if response == 1: # QDialog.DialogCode.Accepted == 1
            self.settings.setValue("delete_images", prefs_dialog.delete_images_checkbox.isChecked())
            self.is_delete_checked = self.settings.value("delete_images", type=bool)

    def displayFullScreen(self, state):
        """Check the state of checkable fullscreen_act. If True, show the 
        main window as fullscreen."""
        if state: self.showFullScreen()
        else: self.showNormal()

    def showAboutDialog(self):
        """Display the application's about dialog."""
        name = QApplication.applicationName()
        app_version = QApplication.applicationVersion()
        QMessageBox.about(self, "Image Manager",
            f"""<h3 style='text-align:center'>{name}</h3>
            <p style='font-weight: normal'>The <b><i>Image Manager GUI</i></b> 
            demonstrates how to build an application for managing photos. This 
            program also examines some of the common features found in many GUIs.</p>
            <p style='font-weight: normal'>This application is part of
            <b><i>Building Custom UIs with PyQt</i></b>.</p>
            <p style='font-weight: normal'>Designed by: <b>Joshua Willman</b></p>
            <p style='font-weight: normal'>Icons created by: <b>Joshua Willman</b></p>
            <p>Version {app_version}</p>""")

    def getInitialSettings(self):
        """Get initial settings of the application using QSettings upon startup."""
        position = self.settings.value("position", QPoint(200, 0))
        size = self.settings.value("size", QSize(800, 500))
        self.is_delete_checked = self.settings.value("delete_images", type=bool) 
        # restoreState() is used here to restore the image_preview_dock widget
        self.restoreState(self.settings.value("window_state", bytes(QByteArray())))

        self.resize(size)
        self.move(position)
        return self.is_delete_checked
    
    def saveSettings(self):
        """Save the settings of the application."""
        self.settings.setValue("position", self.pos())
        self.settings.setValue("size", self.size())
        self.settings.setValue("window_state", self.saveState())

    def closeEvent(self, event):
        """Save the application's settings in the closeEvent()."""
        self.saveSettings()
        event.setAccepted(True)

# NOTE: Left here for your reference and should you decide to run the application
# from main_window instead of main.py. Should you do so, you will also need to 
# modify the relative imports in the beginning. 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("../icons/images_icon.png"))
    window = MainWindow()
    sys.exit(app.exec())