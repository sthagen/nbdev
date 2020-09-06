# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/06_cli.ipynb (unless otherwise specified).

__all__ = ['nbdev_upgrade', 'nbdev_build_lib', 'nbdev_update_lib', 'nbdev_diff_nbs', 'nbdev_test_nbs', 'make_readme',
           'nbdev_build_docs', 'nbdev_nb2md', 'nbdev_detach', 'nbdev_read_nbs', 'nbdev_trust_nbs', 'nbdev_fix_merge',
           'bump_version', 'nbdev_bump_version', 'nbdev_conda_package', 'nbdev_install_git_hooks', 'nbdev_new']

# Cell
from .imports import *
from .export import *
from .sync import *
from .merge import *
from .export2html import *
from .test import *
from .conda import *
from fastscript import call_parse,Param,bool_arg
from subprocess import check_output,STDOUT

# Cell
import re,nbformat
from .export import _mk_flag_re, _re_all_def
from .flags import parse_line

# Internal Cell
def _code_patterns_and_replace_fns():
    "Return a list of pattern/function tuples that can migrate flags used in code cells"
    patterns_and_replace_fns = []

    def _replace_fn(magic, m):
        "Return a magic flag for a comment flag matched in `m`"
        if not m.groups() or not m.group(1): return f'%{magic}'
        return f'%{magic}' if m.group(1) is None else f'%{magic} {m.group(1)}'

    def _add_pattern_and_replace_fn(comment_flag, magic_flag, n_params=(0,1)):
        "Add a pattern/function tuple to go from comment to magic flag"
        pattern = _mk_flag_re(False, comment_flag, n_params, "")
        # note: fn has to be single arg so we can use it in `pattern.sub` calls later
        patterns_and_replace_fns.append((pattern, partial(_replace_fn, magic_flag)))

    _add_pattern_and_replace_fn('default_exp', 'nbdev_default_export', 1)
    _add_pattern_and_replace_fn('exports', 'nbdev_export_and_show')
    _add_pattern_and_replace_fn('exporti', 'nbdev_export_internal')
    _add_pattern_and_replace_fn('export', 'nbdev_export')
    _add_pattern_and_replace_fn('hide_input', 'nbdev_hide_input', 0)
    _add_pattern_and_replace_fn('hide_output', 'nbdev_hide_output', 0)
    _add_pattern_and_replace_fn('hide', 'nbdev_hide', 0) # keep at index 6 - see _migrate2magic
    _add_pattern_and_replace_fn('default_cls_lvl', 'nbdev_default_class_level', 1)
    _add_pattern_and_replace_fn('collapse[_-]output', 'nbdev_collapse_output', 0)
    _add_pattern_and_replace_fn('collapse[_-]show', 'nbdev_collapse_input open', 0)
    _add_pattern_and_replace_fn('collapse[_-]hide', 'nbdev_collapse_input', 0)
    _add_pattern_and_replace_fn('collapse', 'nbdev_collapse_input', 0)
    for flag in Config().get('tst_flags', '').split('|'):
        if flag.strip():
            _add_pattern_and_replace_fn(f'all_{flag}', f'nbdev_{flag}_test all', 0)
            _add_pattern_and_replace_fn(flag, f'nbdev_{flag}_test', 0)
    patterns_and_replace_fns.append(
        (_re_all_def, lambda m: '%nbdev_add2all ' + ','.join(parse_line(m.group(1)))))
    return patterns_and_replace_fns

# Internal Cell
class CellMigrator():
    "Can migrate a cell using `patterns_and_replace_fns`"
    def __init__(self, patterns_and_replace_fns):
        self.patterns_and_replace_fns,self.upd_count,self.first_cell=patterns_and_replace_fns,0,None
    def __call__(self, cell):
        if self.first_cell is None: self.first_cell = cell
        for pattern, replace_fn in self.patterns_and_replace_fns:
            source=cell.source
            cell.source=pattern.sub(replace_fn, source)
            if source!=cell.source: self.upd_count+=1

# Internal Cell
def _migrate2magic(nb):
    "Migrate a single notebook"
    # migrate #hide in markdown
    m=CellMigrator(_code_patterns_and_replace_fns()[6:7])
    [m(cell) for cell in nb.cells if cell.cell_type=='markdown']
    # migrate everything in code_patterns_and_replace_fns in code cells
    m=CellMigrator(_code_patterns_and_replace_fns())
    [m(cell) for cell in nb.cells if cell.cell_type=='code']
    imp,fc='from nbdev import *',m.first_cell
    if m.upd_count!=0 and fc is not None and imp not in fc.get('source', ''):
        nb.cells.insert(0, nbformat.v4.new_code_cell(imp, metadata={'hide_input': True}))
    NotebookNotary().sign(nb)
    return nb

# Internal Cell
_details_description_css = """\n
/*Added by nbdev add_collapse_css*/
details.description[open] summary::after {
    content: attr(data-open);
}

details.description:not([open]) summary::after {
    content: attr(data-close);
}

details.description summary {
    text-align: right;
    font-size: 15px;
    color: #337ab7;
    cursor: pointer;
}

details + div.output_wrapper {
    /* show/hide code */
    margin-top: 25px;
}

div.input + details {
    /* show/hide output */
    margin-top: -25px;
}
/*End of section added by nbdev add_collapse_css*/"""

def _add_collapse_css(doc_path=None):
    "Update customstyles.css so that collapse components can be used in HTML pages"
    fn = (Path(doc_path) if doc_path else Config().doc_path/'css')/'customstyles.css'
    with open(fn) as f:
        if 'details.description' in f.read():
            print('details.description already styled in customstyles.css, no changes made')
        else:
            with open(fn, 'a') as f: f.write(_details_description_css)
            print('details.description styles added to customstyles.css')

# Cell
@call_parse
def nbdev_upgrade(migrate2magic:Param("Migrate all notebooks in `nbs_path` to use magic flags", bool_arg)=True,
                  add_collapse_css:Param("Add css for \"#collapse\" components", bool_arg)=True):
    "Update an existing nbdev project to use the latest features"
    if migrate2magic:
        for fname in Config().nbs_path.glob('*.ipynb'):
            print('Migrating', fname)
            nbformat.write(_migrate2magic(read_nb(fname)), str(fname), version=4)
    if add_collapse_css: _add_collapse_css()

# Cell
@call_parse
def nbdev_build_lib(fname:Param("A notebook name or glob to convert", str)=None):
    "Export notebooks matching `fname` to python modules"
    write_tmpls()
    notebook2script(fname=fname)

# Cell
@call_parse
def nbdev_update_lib(fname:Param("A notebook name or glob to convert", str)=None):
    "Propagates any change in the modules matching `fname` to the notebooks that created them"
    script2notebook(fname=fname)

# Cell
@call_parse
def nbdev_diff_nbs():
    "Prints the diff between an export of the library in notebooks and the actual modules"
    diff_nb_script()

# Cell
def _test_one(fname, flags=None, verbose=True):
    print(f"testing {fname}")
    start = time.time()
    try:
        test_nb(fname, flags=flags)
        return True,time.time()-start
    except Exception as e:
        if "ZMQError" in str(e): _test_one(item, flags=flags, verbose=verbose)
        if verbose: print(f'Error in {fname}:\n{e}')
        return False,time.time()-start

# Cell
@call_parse
def nbdev_test_nbs(fname:Param("A notebook name or glob to convert", str)=None,
                   flags:Param("Space separated list of flags", str)=None,
                   n_workers:Param("Number of workers to use", int)=None,
                   verbose:Param("Print errors along the way", bool)=True,
                   timing:Param("Timing each notebook to see the ones are slow", bool)=False,
                   pause:Param("Pause time (in secs) between notebooks to avoid race conditions", float)=0.2):
    "Test in parallel the notebooks matching `fname`, passing along `flags`"
    if flags is not None: flags = flags.split(' ')
    if fname is None:
        files = [f for f in Config().nbs_path.glob('*.ipynb') if not f.name.startswith('_')]
    else: files = glob.glob(fname)
    files = [Path(f).absolute() for f in sorted(files)]
    if n_workers is None: n_workers = 0 if len(files)==1 else min(num_cpus(), 8)
    # make sure we are inside the notebook folder of the project
    os.chdir(Config().nbs_path)
    results = parallel(_test_one, files, flags=flags, verbose=verbose, n_workers=n_workers, pause=pause)
    passed,times = [r[0] for r in results],[r[1] for r in results]
    if all(passed): print("All tests are passing!")
    else:
        msg = "The following notebooks failed:\n"
        raise Exception(msg + '\n'.join([f.name for p,f in zip(passed,files) if not p]))
    if timing:
        for i,t in sorted(enumerate(times), key=lambda o:o[1], reverse=True):
            print(f"Notebook {files[i].name} took {int(t)} seconds")

# Cell
_re_index = re.compile(r'^(?:\d*_|)index\.ipynb$')

# Cell
def make_readme():
    "Convert the index notebook to README.md"
    index_fn = None
    for f in Config().nbs_path.glob('*.ipynb'):
        if _re_index.match(f.name): index_fn = f
    assert index_fn is not None, "Could not locate index notebook"
    print(f"converting {index_fn} to README.md")
    convert_md(index_fn, Config().config_file.parent, jekyll=False)
    n = Config().config_file.parent/index_fn.with_suffix('.md').name
    shutil.move(n, Config().config_file.parent/'README.md')
    if Path(Config().config_file.parent/'PRE_README.md').is_file():
        with open(Config().config_file.parent/'README.md', 'r') as f: readme = f.read()
        with open(Config().config_file.parent/'PRE_README.md', 'r') as f: pre_readme = f.read()
        with open(Config().config_file.parent/'README.md', 'w') as f: f.write(f'{pre_readme}\n{readme}')

# Cell
@call_parse
def nbdev_build_docs(fname:Param("A notebook name or glob to convert", str)=None,
                     force_all:Param("Rebuild even notebooks that haven't changed", bool_arg)=False,
                     mk_readme:Param("Also convert the index notebook to README", bool_arg)=True,
                     n_workers:Param("Number of workers to use", int)=None,
                     pause:Param("Pause time (in secs) between notebooks to avoid race conditions", float)=0.2):
    "Build the documentation by converting notebooks mathing `fname` to html"
    notebook2html(fname=fname, force_all=force_all, n_workers=n_workers, pause=pause)
    if fname is None: make_sidebar()
    if mk_readme: make_readme()

# Cell
@call_parse
def nbdev_nb2md(fname:Param("A notebook file name to convert", str),
                dest:Param("The destination folder", str)='.',
                img_path:Param("Folder to export images to")="",
                jekyll:Param("To use jekyll metadata for your markdown file or not", bool_arg)=False,):
    "Convert the notebook in `fname` to a markdown file"
    nb_detach_cells(fname, dest=img_path)
    convert_md(fname, dest, jekyll=jekyll, img_path=img_path)

# Cell
@call_parse
def nbdev_detach(path_nb:Param("Path to notebook"),
                 dest:Param("Destination folder", str)="",
                 use_img:Param("Convert markdown images to img tags", bool_arg)=False):
    "Export cell attachments to `dest` and update references"
    nb_detach_cells(path_nb, dest=dest, use_img=use_img)

# Cell
@call_parse
def nbdev_read_nbs(fname:Param("A notebook name or glob to convert", str)=None):
    "Check all notebooks matching `fname` can be opened"
    files = Config().nbs_path.glob('**/*.ipynb') if fname is None else glob.glob(fname)
    for nb in files:
        try: _ = read_nb(nb)
        except Exception as e:
            print(f"{nb} is corrupted and can't be opened.")
            raise e

# Cell
@call_parse
def nbdev_trust_nbs(fname:Param("A notebook name or glob to convert", str)=None,
                    force_all:Param("Trust even notebooks that haven't changed", bool)=False):
    "Trust noteboks matching `fname`"
    check_fname = Config().nbs_path/".last_checked"
    last_checked = os.path.getmtime(check_fname) if check_fname.exists() else None
    files = Config().nbs_path.glob('**/*.ipynb') if fname is None else glob.glob(fname)
    for fn in files:
        if last_checked and not force_all:
            last_changed = os.path.getmtime(fn)
            if last_changed < last_checked: continue
        nb = read_nb(fn)
        if not NotebookNotary().check_signature(nb): NotebookNotary().sign(nb)
    check_fname.touch(exist_ok=True)

# Cell
@call_parse
def nbdev_fix_merge(fname:Param("A notebook filename to fix", str),
                    fast:Param("Fast fix: automatically fix the merge conflicts in outputs or metadata", bool)=True,
                    trust_us:Param("Use local outputs/metadata when fast mergning", bool)=True):
    "Fix merge conflicts in notebook `fname`"
    fix_conflicts(fname, fast=fast, trust_us=trust_us)

# Cell
def bump_version(version, part=2):
    version = version.split('.')
    version[part] = str(int(version[part]) + 1)
    for i in range(part+1, 3): version[i] = '0'
    return '.'.join(version)

# Cell
@call_parse
def nbdev_bump_version(part:Param("Part of version to bump", int)=2):
    "Increment version in `settings.py` by one"
    cfg = Config()
    print(f'Old version: {cfg.version}')
    cfg.d['version'] = bump_version(Config().version, part)
    cfg.save()
    update_version()
    print(f'New version: {cfg.version}')

# Cell
@call_parse
def nbdev_conda_package(path:Param("Path where package will be created", str)='conda',
                        do_build:Param("Run `conda build` step", bool)=True,
                        build_args:Param("Additional args (as str) to send to `conda build`", str)='',
                        do_upload:Param("Run `anaconda upload` step", bool)=True,
                        upload_user:Param("Optional user to upload package to")=None):
    "Create a `meta.yaml` file ready to be built into a package, and optionally build and upload it"
    write_conda_meta(path)
    cfg = Config()
    name = cfg.get('lib_name')
    out = f"Done. Next steps:\n```\`cd {path}\n"""
    out_upl = f"anaconda upload $CONDA_PREFIX/conda-bld/noarch/{name}-{cfg.get('version')}-py_0.tar.bz2"
    if not do_build:
        print(f"{out}conda build .\n{out_upl}\n```")
        return

    os.chdir(path)
    try: res = check_output(f"conda build {build_args} .".split()).decode()
    except subprocess.CalledProcessError as e: print(f"{e.output}\n\nBuild failed.")
    if 'to anaconda.org' in res: return
    if 'anaconda upload' not in res:
        print(f"{res}\n\Build failed.")
        return

    upload_str = re.findall('(anaconda upload .*)', res)[0]
    if upload_user: upload_str = upload_str.replace('anaconda upload ', f'anaconda upload -u {upload_user} ')
    try: res = check_output(upload_str.split(), stderr=STDOUT).decode()
    except subprocess.CalledProcessError as e: print(f"{e.output}\n\nUpload failed.")
    if 'Upload complete' not in res: print(f"{res}\n\nUpload failed.")

# Cell
import subprocess

# Cell
@call_parse
def nbdev_install_git_hooks():
    "Install git hooks to clean/trust notebooks automatically"
    try: path = Config().config_file.parent
    except: path = Path.cwd()
    fn = path/'.git'/'hooks'/'post-merge'
    #Trust notebooks after merge
    with open(fn, 'w') as f:
        f.write("""#!/bin/bash
echo "Trusting notebooks"
nbdev_trust_nbs
"""
        )
    os.chmod(fn, os.stat(fn).st_mode | stat.S_IEXEC)
    #Clean notebooks on commit/diff
    with open(path/'.gitconfig', 'w') as f:
        f.write("""# Generated by nbdev_install_git_hooks
#
# If you need to disable this instrumentation do:
#
# git config --local --unset include.path
#
# To restore the filter
#
# git config --local include.path .gitconfig
#
# If you see notebooks not stripped, checked the filters are applied in .gitattributes
#
[filter "clean-nbs"]
        clean = nbdev_clean_nbs --read_input_stream True
        smudge = cat
        required = true
[diff "ipynb"]
        textconv = nbdev_clean_nbs --disp True --fname
""")
    cmd = "git config --local include.path ../.gitconfig"
    print(f"Executing: {cmd}")
    result = subprocess.run(cmd.split(), shell=False, check=False, stderr=subprocess.PIPE)
    if result.returncode == 0:
        print("Success: hooks are installed and repo's .gitconfig is now trusted")
    else:
        print("Failed to trust repo's .gitconfig")
        if result.stderr: print(f"Error: {result.stderr.decode('utf-8')}")
    try: nb_path = Config().nbs_path
    except: nb_path = Path.cwd()
    with open(nb_path/'.gitattributes', 'w') as f:
        f.write("""**/*.ipynb filter=clean-nbs
**/*.ipynb diff=ipynb
"""
               )

# Cell
_template_git_repo = "https://github.com/fastai/nbdev_template.git"

# Cell
@call_parse
def nbdev_new(name: Param("A directory to create the project in", str),
              template_git_repo: Param("url to template repo", str)=_template_git_repo):
    "Create a new nbdev project with a given name."

    path = Path(f"./{name}").absolute()

    if path.is_dir():
        print(f"Directory {path} already exists. Aborting.")
        return

    print(f"Creating a new nbdev project {name}.")

    def rmtree_onerror(func, path, exc_info):
        "Use with `shutil.rmtree` when you need to delete files/folders that might be read-only."
        os.chmod(path, stat.S_IWRITE)
        func(path)

    try:
        subprocess.run(['git', 'clone', f'{template_git_repo}', f'{path}'], check=True, timeout=5000)
        # Note: on windows, .git is created with a read-only flag
        shutil.rmtree(path/".git", onerror=rmtree_onerror)
        subprocess.run("git init".split(), cwd=path, check=True)
        subprocess.run("git add .".split(), cwd=path, check=True)
        subprocess.run("git commit -am \"Initial\"".split(), cwd=path, check=True)

        print(f"Created a new repo for project {name}. Please edit settings.ini and run nbdev_build_lib to get started.")
    except Exception as e:
        print("An error occured while copying nbdev project template:")
        print(e)
        if os.path.isdir(path):
            try:
                shutil.rmtree(path, onerror=rmtree_onerror)
            except Exception as e2:
                print(f"An error occured while cleaning up. Failed to delete {path}:")
                print(e2)