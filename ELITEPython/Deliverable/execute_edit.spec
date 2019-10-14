# -*- mode: python -*-
import sys
sys.setrecursionlimit(5000)

block_cipher = None



a = Analysis(['execute.py'],
             pathex=['D:\\users\\jdavid\\Programming\\GitHub\\SchedulingSimulator\\ELITEPython\\Deliverable'],
             binaries=[],
             datas=[('Readme.txt', '.'), 
                    ('D:/users/jdavid/Programming/GitHub/SchedulingSimulator/ELITEPython/Deliverable/original_data/productionfile', 'original_data/productionfile'),
                    ('D:/users/jdavid/Programming/GitHub/SchedulingSimulator/ELITEPython/Deliverable/original_data/packagingfile_old', 'original_data/packagingfile_old'),
                    ('D:/users/jdavid/Programming/GitHub/SchedulingSimulator/ELITEPython/Deliverable/config.ini', '.')],
             hiddenimports=['numpy.core._dtype_ctypes', 'probdist'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='execute',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True, 
	   icon=r'D:\users\jdavid\Programming\GitHub\SchedulingSimulator\ELITEPython\Deliverable\calendar_icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='execute')
