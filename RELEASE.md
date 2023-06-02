Release type: patch

Custom codegen plugins will fail to write files if the plugin is trying to put the
file anywhere other than the root output directory (since the child directories do
not yet exist).  This change will create the child directory if necessary before
attempting to write the file.
