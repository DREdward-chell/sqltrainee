"""Execute clean bundled notebooks, without touching learners' answers/progress."""
from pathlib import Path
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
import sys
for name in ('training.ipynb', 'exam.ipynb'):
    nb = nbformat.read(Path('/opt/sqltrainee') / name, as_version=4)
    nbformat.validate(nb)
    km = KernelManager(kernel_name='python3')
    km.kernel_spec.argv = [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}']
    try:
        NotebookClient(nb, km=km, timeout=60,
                       resources={'metadata': {'path': '/var/lib/sqltrainee/work'}}).execute()
        assert not [o for c in nb.cells if c.cell_type == 'code'
                    for o in c.outputs if o.output_type == 'error']
        print('PASS:', name)
    finally:
        if km.has_kernel:
            km.shutdown_kernel(now=True)
