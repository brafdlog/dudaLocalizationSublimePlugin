import sublime
import sublime_plugin
import os
import os.path
from functools import partial
import re

SYSTEM_ROOT_PATH = os.path.abspath(os.sep)
SEPARATOR = os.pathsep
KEY_PREFIX = 'ui.ed.'

# This script takes the selected text and replaces it with a localization key.
# If the selected text already exists in the CommonStrings file it finds the right
# key and replaces it. If this is a new text, the user is prompted to enter a new localization
# key and that key and value is added to the common strings.
class dLocalizeCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        view = self.view
        window = view.window()
        sel = view.sel()
        currentFilePath = view.file_name()

        dudaRootFolderPath = self.getDudaRootFolderPath(currentFilePath)
        # This will usually happen if the file we are looking at is not inside DudaRoot
        if dudaRootFolderPath is SYSTEM_ROOT_PATH:
            sublime.error_message('Could not find DudaRoot folder path')
            return
        
        print('dudaRootFolderPath: ' + dudaRootFolderPath);

        stringsFilePath = os.path.join(dudaRootFolderPath, 'src', 'resources', 'English', 'strings', 'CommonStrings.ed.properties')
        stringsFile = open(stringsFilePath)
        stringsFileLines = stringsFile.readlines()
        stringsFile.close()

        selectedRegion = sel[0]
        selectionText = view.substr(selectedRegion)
        selectionText = selectionText.replace('\'', '')
        if selectionText:
            localizationKey = self.getExistingKeyForText(stringsFileLines, selectionText)
            if localizationKey: # if this text already exists in the string file
                self.replaceSelectionWithLocalizationKey(localizationKey)
            else: # if this is a new string that we need to add to the strings file
                doneHandler = partial(self.replaceSelectionAndAddNewLocalizationKey, selectionText, stringsFilePath, stringsFileLines)
                window.show_input_panel('Write localization key', '', doneHandler, None, None)
        else:
            sublime.error_message('No text was highlighted')

    # Replace the current selection with the given localization key and add the key to the strings file
    def replaceSelectionAndAddNewLocalizationKey(self, selectionText, stringsFilePath, stringsFileLines, localizationKey):
        self.replaceSelectionWithLocalizationKey(localizationKey)
        stringsFileLines.append(KEY_PREFIX + localizationKey + '=' + selectionText + '\n')

        # Want to keep them sorted alphabetically
        self.sort_nicely(stringsFileLines)

        stringsFile = open(stringsFilePath, 'w') # to clear the file
        stringsFile.write(''.join(stringsFileLines))
        stringsFile.close()

    # Replace the current selection with the given localization key
    def replaceSelectionWithLocalizationKey(self, localizationKey):
        keyWithoutPrefix = self.removePrefix(localizationKey, KEY_PREFIX)
        self.view.run_command("insert", {"characters": 'str(\'' + keyWithoutPrefix + '\')'})

    # if the string starts with the given prefix return the same string without that prefix
    def removePrefix(self, string, prefixToRemove):
        if string.startswith(prefixToRemove):
            return string[len(prefixToRemove):]
        return string

    # Find existing localization key for the given text. Returns the key if exists,
    # otherwise returns None
    def getExistingKeyForText(self, stringsFileLines, text):
        for line in stringsFileLines:
            if line.lower().strip().endswith('=' + text.lower()):
                key = line.split('=')
                return key[0];
        return None

    # Recursively searches for the duda root folder starting from the current active file
    # and up through it's ancestors
    def getDudaRootFolderPath(self, path):
        if not path or path is SYSTEM_ROOT_PATH or path.endswith(os.path.join('duda', 'DudaRoot')):
            return path
        parentFolderPath = self.getParentDirectoryPath(path)
        return self.getDudaRootFolderPath(parentFolderPath)

    def getParentDirectoryPath(self, path):
        return os.path.abspath(os.path.join(path, os.pardir))

    def sort_nicely(self, listToSort):
        """ Sort the given list in the way that humans expect - numbers inside strings are sorted correctly
        """
        convert = lambda text: int(text) if text.isdigit() else text
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
        listToSort.sort( key=alphanum_key )
