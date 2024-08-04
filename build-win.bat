pyinstaller --name "jaKB" --icon res/lang.ico --windowed jaKB.py
xcopy res dist\jaKB\res /I
xcopy src dist\jaKB\src /I
xcopy config.ini dist\jaKB /I
xcopy README.md dist\jaKB /I
xcopy requirements.txt dist\jaKB /I
rmdir build /s /q


