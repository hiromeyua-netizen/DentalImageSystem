"""

Launch the Dental Imaging application (Phase 1).



Equivalent to running from the repository root::



    python -m dental_imaging.main



Optional flags: ``--no-fullscreen``, ``--no-auto-preview``, ``--app-config PATH``,

``--camera-config PATH``.

"""



import sys

from pathlib import Path



PROJECT_ROOT = Path(__file__).parent.parent

if str(PROJECT_ROOT) not in sys.path:

    sys.path.insert(0, str(PROJECT_ROOT))



from dental_imaging.main import main



if __name__ == "__main__":

    sys.exit(main())

