"""Keep SQL magics as editable SQL in VS Code notebooks."""
def format_cell(source):
    return source

def format_markdown(source):
    return source

def cell_metadata(source):
    return {"vscode": {"languageId": "sql"}} if source.startswith(("%%check", "%%sql", "%%answer")) else {}
