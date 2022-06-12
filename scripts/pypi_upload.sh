echo "clear old builds directory"
rm -rf build/*
rm -rf dist/*
python3 setup.py sdist
twine upload dist/*
rm -rf build/*
echo "done."