pyinstaller --noconfirm --onedir --console --add-data "venv\Lib\site-packages\customtkinter;customtkinter/" --copy-metadata "tqdm" --copy-metadata "regex" --copy-metadata "requests" --copy-metadata "packaging" --copy-metadata "filelock" --copy-metadata "numpy" --copy-metadata "tokenizers" --copy-metadata "importlib_metadata" --add-data "promptflow\res;promptflow\res\" "promptflow\__main__.py"