import difflib

def calculate_diffs(modified_files_dict, codebase):
    diffs = {}
    for path, new_code in modified_files_dict.items():
        original_code = codebase.get(path, '')
        diff = difflib.unified_diff(
            original_code.splitlines(keepends=True),
            new_code.splitlines(keepends=True),
            fromfile=f'a/{path}',
            tofile=f'b/{path}',
        )
        diffs[path] = ''.join(diff)
    return diffs
