from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from setuptools import setup

module_path = Path(__file__).parent / "pilther" / "_build_zig.py"
spec = spec_from_file_location("pilther_build_zig", module_path)
if spec is None or spec.loader is None:
    raise RuntimeError("Failed to load build hook module")
module = module_from_spec(spec)
spec.loader.exec_module(module)
build_py = module.build_py

cmdclass = {"build_py": build_py}
if hasattr(module, "bdist_wheel"):
    cmdclass["bdist_wheel"] = module.bdist_wheel


setup(
    cmdclass=cmdclass,
)
