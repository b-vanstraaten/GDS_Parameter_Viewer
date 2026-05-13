for version in 3.10 3.11 3.12 3.13 3.14; do
    echo "--- Python $version ---"
    uv run --python $version python -c "from GDS_Parameter_Viewer.GDSViewer import GDSViewer; print('OK')"
done