pip install -r req.txt

WORKDIR="src"
MODULE="ProcessController"

cd $WORKDIR && flake8 && mypy .
python -m $MODULE