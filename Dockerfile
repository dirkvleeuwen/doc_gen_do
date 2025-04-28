<file name=generators.py path=/Users/latex-user/Documents/doc_gen_do/instruments/exports># (other imports)
import subprocess

# (other code)

# Replace the subprocess.run call invoking pdflatex with the try/except block
try:
    subprocess.run(
        ['pdflatex', '-interaction=nonstopmode', '-output-directory', tmpdir, texfile],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )
except subprocess.CalledProcessError as e:
    # Raise a descriptive error including the LaTeX log
    raise RuntimeError(
        f"LaTeX compilatie mislukt (exit {e.returncode}):\n{e.stderr}"
    )

# (rest of the code)